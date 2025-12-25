import logging
import requests
from typing import List, Optional, Literal
from app.config.settings import get_settings
from app.services.shopify.models import ProductResponse, OrderResponse, PolicyItem, ShopInfo
from app.utils.retry import network_retry

logger = logging.getLogger(__name__)
settings = get_settings()

class ShopifyController:
    def __init__(self):
        self.base_url = f"https://{settings.SHOPIFY_STORE}.myshopify.com"
        self.admin_graphql_url = f"{self.base_url}/admin/api/2025-10/graphql.json"
        self.graphql_url = f"{self.base_url}/api/2025-10/graphql.json"
        self.storefront_token = settings.SHOPIFY_STOREFRONT_ACCESS_TOKEN
        self.admin_token = settings.SHOPIFY_ADMIN_ACCESS_TOKEN

    @network_retry()
    def search_products(self, search_term: str) -> List[ProductResponse]:
        try:
            headers = {
                "Content-Type": "application/json",
                "X-Shopify-Storefront-Access-Token": self.storefront_token
            }

            gql_query = """
            query SearchProducts($query: String!) {
              search(first: 10, query: $query) {
                edges {
                  node {
                    __typename
                    ... on Product {
                      id
                      title
                      description
                      handle
                      onlineStoreUrl
                      images(first: 1) {
                        edges {
                          node {
                            url
                          }
                        }
                      }
                      priceRange {
                        minVariantPrice {
                          amount
                          currencyCode
                        }
                      }
                      variants(first: 5) {
                        nodes {
                          id
                          title
                          priceV2 {
                            amount
                            currencyCode
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
            """

            variables = {"query": search_term}

            resp = requests.post(
                self.graphql_url,
                json={"query": gql_query, "variables": variables},
                headers=headers
            )
            # raise exception jika error HTTP
            resp.raise_for_status()

            data = resp.json()

            # cek jika ada error dari graphQL
            if "errors" in data:
                logger.error(f"Shopify GraphQL error: {data['errors']}")
                return []

            # parse products
            products: List[ProductResponse] = []

            for edge in data.get("data", {}).get("search", {}).get("edges", []):
                node = edge.get("node", {})
                if node.get("__typename") != "Product":
                    continue  # skip non-Product types

                # ambil gambar pertama jika ada
                image_url = None
                images = node.get("images", {}).get("edges", [])
                if images and len(images) > 0:
                    image_url = images[0].get("node", {}).get("url")

                # ambil harga utama dari priceRange
                price_info = node.get("priceRange", {}).get("minVariantPrice", {})
                price_amount = float(price_info.get("amount", 0))
                price_currency = price_info.get("currencyCode", "")

                variant_list = []
                for v in node.get("variants", {}).get("nodes", []):
                    price_v2 = v.get("priceV2", {})
                    variant_list.append({
                        "id": v.get("id"),
                        "title": v.get("title"),
                        "price": float(price_v2.get("amount", 0)),
                        "currency": price_v2.get("currencyCode", "")
                    })

                product_resp = ProductResponse(
                    id=node.get("id"),
                    title=node.get("title"),
                    description=node.get("description"),
                    price_amount=price_amount,
                    price_currency=price_currency,
                    image_url=image_url,
                    product_url=node.get("onlineStoreUrl"),
                    variants=variant_list
                )

                products.append(product_resp)

            return products

        except Exception as e:
            logger.exception("Error searching products in Shopify", exc_info=e)
            raise
  
    @network_retry()
    def order_lookup(self, order_id: str) -> Optional[List[OrderResponse]]:
        try:
            headers = {
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": self.admin_token
            }

            if not order_id:
                raise ValueError("order_id must be provided.")

            # GraphQL query
            gql_query = """
              query getOrder($query: String!) {
                orders(first: 1, query: $query) {
                  edges {
                    node {
                      id
                      name
                      email
                      displayFulfillmentStatus
                      displayFinancialStatus
                      createdAt
                      lineItems(first: 20) {
                        edges {
                          node {
                            title
                            quantity
                            originalTotalSet {
                              shopMoney {
                                amount
                                currencyCode
                              }
                            }
                          }
                        }
                      }
                      fulfillments(first: 5) {
                        status
                        trackingInfo(first: 5) {
                          company
                          number
                          url
                        }
                      }
                    }
                  }
                }
              }

            """

            variables = {"query": f"name:{order_id}"}

            resp = requests.post(
                self.admin_graphql_url,
                json={"query": gql_query, "variables": variables},
                headers=headers
            )
            resp.raise_for_status()

            data = resp.json()

            # Cek jika errors
            if "errors" in data:
                logger.error(data["errors"])
                raise Exception(data["errors"])

            orders = data.get("data", {}).get("orders", {}).get("edges", [])

            if not orders:
                # Jika tidak ada order
                logger.info(f"No orders found for order_id: {order_id}")
                return "[]"

            results = []

            for edge in orders:
                order_node = edge.get("node", {})

                # Parse line items
                line_items = []
                for item_edge in order_node.get("lineItems", {}).get("edges", []):
                    item = item_edge.get("node", {})
                    money = item.get("originalTotalSet", {}).get("shopMoney", {})
                    line_items.append({
                        "title": item.get("title"),
                        "quantity": item.get("quantity"),
                        "amount": float(money.get("amount", 0)),
                        "currency": money.get("currencyCode", "")
                    })

                # Parse fulfillments and tracking info
                fulfillments = []
                for f in order_node.get("fulfillments", []):
                    tracking_data = []
                    for t in f.get("trackingInfo", []):
                        tracking_data.append({
                            "company": t.get("company"),
                            "number": t.get("number"),
                            "url": t.get("url")
                        })
                    fulfillments.append({
                        "status": f.get("status"),
                        "tracking_info": tracking_data
                    })

                total_price = sum(li["amount"] for li in line_items)

                order_info = OrderResponse(
                    id=order_node.get("id"),
                    name=order_node.get("name"),
                    email=order_node.get("email"),
                    total_price=total_price,
                    currency=line_items[0]["currency"] if line_items else "",
                    line_items=line_items,
                    fulfillment_status=order_node.get("displayFulfillmentStatus"),
                    financial_status=order_node.get("displayFinancialStatus"),
                    fulfillments=fulfillments,
                    created_at=order_node.get("createdAt"),
                )

                results.append(order_info)


            return results

        except Exception as e:
            logger.exception("Error looking up order in Shopify", exc_info=e)
            raise

    @network_retry()
    def get_policies(self, policy_type: Literal["privacy", "terms", "refund", "shipping"]) -> Optional[PolicyItem]:
        """
        Mengambil satu policy dari Shopify Admin REST API (policies.json)
        berdasarkan policy_type: ["privacy", "terms", "refund", "shipping"]
        """
        try:
            headers = {
                "X-Shopify-Access-Token": self.admin_token,
                "Content-Type": "application/json"
            }

            url = f"{self.base_url}/admin/api/2025-10/policies.json"
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()

            policies_list = resp.json().get("policies", [])

            # Default kosong jika tidak ditemukan
            result = {"title": None, "body": None, "url": None}

            for pol in policies_list:
                handle = pol.get("handle", "").lower()

                # Lebih tepat: cek substring yg sesuai
                if policy_type == "privacy" and "privacy" in handle:
                    result = {
                        "title": pol.get("title"),
                        "body": pol.get("body"),
                    }
                    break
                elif policy_type == "terms" and "terms" in handle:
                    result = {
                        "title": pol.get("title"),
                        "body": pol.get("body"),
                    }
                    break
                elif policy_type == "refund" and "refund" in handle:
                    result = {
                        "title": pol.get("title"),
                        "body": pol.get("body"),
                    }
                    break
                elif policy_type == "shipping" and "shipping" in handle:
                    result = {
                        "title": pol.get("title"),
                        "body": pol.get("body"),
                    }
                    break

            return PolicyItem(**result)

        except Exception as e:
            logger.exception("Error fetching Shopify policies via REST API", exc_info=e)
            raise

    
    @network_retry()
    def get_shop_info(self) -> Optional[ShopInfo]:
        try:
            headers = {
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": self.admin_token
            }

            gql_query = """
              query {
                shop {
                  name
                  email
                  myshopifyDomain
                  contactEmail
                  primaryDomain {
                    host
                  }
                  billingAddress {
                    address1
                    address2
                    city
                    province
                    country
                    zip
                    phone
                  }
                }
              }
            """
            resp = requests.post(
                self.admin_graphql_url,
                json={"query": gql_query},
                headers=headers
            )
            resp.raise_for_status()

            data = resp.json()

            if "errors" in data:
                logger.error(f"Shopify GraphQL error: {data['errors']}")
                return None

            shop_data = data.get("data", {}).get("shop", {})

            if not shop_data:
                logger.info("No shop information found")
                return None

            return ShopInfo(
                name=shop_data.get("name"),
                email=shop_data.get("email"),
                myshopifyDomain=shop_data.get("myshopifyDomain"),
                contactEmail=shop_data.get("contactEmail"),
                primaryDomain=shop_data.get("primaryDomain", {}),
                billingAddress=shop_data.get("billingAddress", {})
            )

        except Exception as e:
            logger.exception("Error fetching Shopify shop info", exc_info=e)
            raise