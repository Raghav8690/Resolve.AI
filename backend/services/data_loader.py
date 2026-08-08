import pandas as pd
import re
from backend.models.schemas import ResolvedTicket, NewTicket, OrderContext
from backend.config import DATA_DIR

def clean_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def load_resolved_tickets() -> pd.DataFrame:
    df = pd.read_csv(f"{DATA_DIR}/resolved_tickets.csv")
    df['clean_description'] = df['description'].apply(clean_text)
    return df

def load_new_tickets() -> pd.DataFrame:
    df = pd.read_csv(f"{DATA_DIR}/new_tickets.csv")
    df['clean_description'] = df['description'].apply(clean_text)
    return df

def load_orders_context() -> pd.DataFrame:
    df = pd.read_csv(f"{DATA_DIR}/orders_context.csv")
    return df

def join_new_tickets_with_orders(new_tickets: pd.DataFrame, orders: pd.DataFrame) -> pd.DataFrame:
    merged = new_tickets.merge(orders, on='order_id', how='left')
    assert merged['order_id'].notna().all(), "Some new tickets failed to join with orders"
    return merged

def load_all():
    resolved = load_resolved_tickets()
    new_tickets = load_new_tickets()
    orders = load_orders_context()
    new_with_orders = join_new_tickets_with_orders(new_tickets, orders)
    return resolved, new_with_orders, orders
