from bs4 import BeautifulSoup
from app.services.shopify.controllers import ShopifyController

def test_search_products():
    controller = ShopifyController()
    # query = " Combed Cotton t-shirt "
    # products = controller.search_products(query)

    # print(f"Search results for query '{query}':")
    # print(products)
    order_number = "#1001"
    order = controller.order_lookup(order_id=order_number)
    print(f"Search results for order number '{order_number}':")
    print(order)

def html_to_text(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text(separator="\n", strip=True)
    return text


def test_get_policy():
    controller = ShopifyController()
    policy_type = "privacy"
    policy = controller.get_policies(policy_type=policy_type)
    text_content = html_to_text(policy.body)
    print("Text content:\n")
    print(text_content)

def get_shop_info():
    controller = ShopifyController()
    shop_info = controller.get_shop_info()
    print("Shop Info:\n")
    shop = shop_info.model_dump_json()
    print(shop)

if __name__ == "__main__":
    get_shop_info()

