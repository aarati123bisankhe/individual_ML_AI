import 'package:flutter/material.dart';

import '../../domain/entities/scan_product.dart';

class CartPage extends StatelessWidget {
  const CartPage({
    super.key,
    required this.products,
    required this.quantities,
    required this.selectedPaymentMethod,
    required this.onAdd,
    required this.onRemove,
    required this.onSelectPaymentMethod,
    required this.onCheckout,
  });

  final List<ScanProduct> products;
  final Map<String, int> quantities;
  final String selectedPaymentMethod;
  final ValueChanged<ScanProduct> onAdd;
  final ValueChanged<ScanProduct> onRemove;
  final ValueChanged<String> onSelectPaymentMethod;
  final VoidCallback onCheckout;

  static const List<String> paymentMethods = [
    'eSewa',
    'Khalti',
    'IME Pay',
    'Card',
  ];

  double get subtotal {
    double total = 0;
    for (final product in products) {
      total += (quantities[product.id] ?? 0) * product.priceNpr;
    }
    return total;
  }

  double get serviceFee => subtotal == 0 ? 0 : 12;

  double get total => subtotal + serviceFee;

  int get itemCount => quantities.values.fold(0, (sum, value) => sum + value);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Your Cart')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF14532D), Color(0xFFD97706)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(24),
              ),
              child: Row(
                children: [
                  Container(
                    width: 48,
                    height: 48,
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.14),
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: const Icon(
                      Icons.shopping_cart_checkout_rounded,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Ready for checkout',
                          style: Theme.of(context).textTheme.titleMedium
                              ?.copyWith(color: Colors.white, fontSize: 18),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          itemCount == 0
                              ? 'No items in your cart yet'
                              : '$itemCount item${itemCount == 1 ? '' : 's'} selected',
                          style: Theme.of(context).textTheme.bodyMedium
                              ?.copyWith(color: const Color(0xFFFFF3E6)),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            if (products.isEmpty)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(color: const Color(0xFFDCE5DF)),
                ),
                child: Text(
                  'No items scanned yet. Go back and scan products to add them here.',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              )
            else ...[
              ...products.map(
                (product) => _CartLineItem(
                  product: product,
                  quantity: quantities[product.id] ?? 0,
                  onAdd: () => onAdd(product),
                  onRemove: () => onRemove(product),
                ),
              ),
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(color: const Color(0xFFDCE5DF)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Payment method',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 14),
                    Wrap(
                      spacing: 10,
                      runSpacing: 10,
                      children: paymentMethods
                          .map(
                            (method) => ChoiceChip(
                              label: Text(method),
                              selected: selectedPaymentMethod == method,
                              onSelected: (_) => onSelectPaymentMethod(method),
                            ),
                          )
                          .toList(),
                    ),
                    const SizedBox(height: 18),
                    _BillRow(
                      label: 'Subtotal',
                      value: 'Rs ${subtotal.toStringAsFixed(0)}',
                    ),
                    _BillRow(
                      label: 'Service fee',
                      value: 'Rs ${serviceFee.toStringAsFixed(0)}',
                    ),
                    _BillRow(
                      label: 'Total',
                      value: 'Rs ${total.toStringAsFixed(0)}',
                      emphasize: true,
                    ),
                    const SizedBox(height: 16),
                    SizedBox(
                      width: double.infinity,
                      child: FilledButton.icon(
                        onPressed: onCheckout,
                        icon: const Icon(Icons.lock_outline_rounded),
                        label: Text('Pay Rs ${total.toStringAsFixed(0)}'),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _CartLineItem extends StatelessWidget {
  const _CartLineItem({
    required this.product,
    required this.quantity,
    required this.onAdd,
    required this.onRemove,
  });

  final ScanProduct product;
  final int quantity;
  final VoidCallback onAdd;
  final VoidCallback onRemove;

  @override
  Widget build(BuildContext context) {
    final lineTotal = product.priceNpr * quantity;
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFDCE5DF)),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  product.name,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 4),
                Text(
                  '${product.category} • Rs ${product.priceNpr.toStringAsFixed(0)} each',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ],
            ),
          ),
          IconButton(
            onPressed: onRemove,
            icon: const Icon(Icons.remove_circle_outline_rounded),
          ),
          Text('$quantity', style: Theme.of(context).textTheme.titleMedium),
          IconButton(
            onPressed: onAdd,
            icon: const Icon(Icons.add_circle_outline_rounded),
          ),
          const SizedBox(width: 6),
          Text(
            'Rs ${lineTotal.toStringAsFixed(0)}',
            style: Theme.of(context).textTheme.titleMedium,
          ),
        ],
      ),
    );
  }
}

class _BillRow extends StatelessWidget {
  const _BillRow({
    required this.label,
    required this.value,
    this.emphasize = false,
  });

  final String label;
  final String value;
  final bool emphasize;

  @override
  Widget build(BuildContext context) {
    final style = emphasize
        ? Theme.of(context).textTheme.titleMedium?.copyWith(fontSize: 18)
        : Theme.of(context).textTheme.bodyMedium;

    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        children: [
          Expanded(child: Text(label, style: style)),
          Text(value, style: style),
        ],
      ),
    );
  }
}
