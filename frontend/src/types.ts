export interface Item {
  id: number
  name: string
  price: number
}

export interface CartItem {
  item_id: number
  name: string
  quantity: number
  unit_price: number
  line_total: number
}

export interface Cart {
  user_id: string
  items: CartItem[]
  subtotal: number
}

export interface OrderItem {
  item_id: number
  name: string
  quantity: number
  unit_price: number
  line_total: number
}

export interface Order {
  id: number
  user_id: string
  items: OrderItem[]
  subtotal: number
  discount_code: string | null
  discount_amount: number
  total: number
  created_at: string
}

export interface DiscountEligible {
  eligible: true
  code: string
  percent: number
}

export interface DiscountIneligible {
  eligible: false
  reason: string
}

export type DiscountGenerateResult = DiscountEligible | DiscountIneligible

export interface Stats {
  items_purchased: number
  total_revenue: number
  discount_codes_issued: number
  total_discount_amount: number
}
