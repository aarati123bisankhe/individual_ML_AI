import 'package:flutter/material.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/info_banner.dart';
import '../../../../core/widgets/section_card.dart';
import '../../data/repositories/scan_to_pay_repository_impl.dart';
import '../../domain/entities/scan_product.dart';
import 'payment_confirmation_page.dart';

class ScanToPayPage extends StatefulWidget {
  const ScanToPayPage({super.key});

  @override
  State<ScanToPayPage> createState() => _ScanToPayPageState();
}

class _ScanToPayPageState extends State<ScanToPayPage> {
  final ScanToPayRepositoryImpl _repository = ScanToPayRepositoryImpl();

  List<ScanProduct> _catalog = const [];
  final Map<String, int> _cart = {};
  bool _isLoading = false;
  String _selectedPaymentMethod = 'eSewa';

  static const List<String> _paymentMethods = [
    'eSewa',
    'Khalti',
    'IME Pay',
    'Card',
  ];

  @override
  void initState() {
    super.initState();
    _loadCatalog();
  }

  Future<void> _loadCatalog() async {
    setState(() {
      _isLoading = true;
    });

    final products = await _repository.getDemoProducts();
    if (mounted) {
      setState(() {
        _catalog = products;
        _isLoading = false;
      });
    }
  }

  void _scanProduct(ScanProduct product) {
    setState(() {
      _cart.update(product.id, (value) => value + 1, ifAbsent: () => 1);
    });
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('${product.name} added to cart'),
        duration: const Duration(milliseconds: 900),
      ),
    );
  }

  void _changeQuantity(ScanProduct product, int delta) {
    final current = _cart[product.id] ?? 0;
    final updated = current + delta;

    setState(() {
      if (updated <= 0) {
        _cart.remove(product.id);
      } else {
        _cart[product.id] = updated;
      }
    });
  }

  double get _subtotal {
    double total = 0;
    for (final product in _catalog) {
      final quantity = _cart[product.id] ?? 0;
      total += quantity * product.priceNpr;
    }
    return total;
  }

  int get _itemCount => _cart.values.fold(0, (sum, value) => sum + value);

  double get _serviceFee => _subtotal == 0 ? 0 : 12;

  double get _total => _subtotal + _serviceFee;

  Future<void> _checkout() async {
    if (_itemCount == 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Scan at least one product first')),
      );
      return;
    }

    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => PaymentConfirmationPage(
          paymentMethod: _selectedPaymentMethod,
          totalAmount: _total,
          itemCount: _itemCount,
        ),
      ),
    );

    if (mounted) {
      setState(() {
        _cart.clear();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final cartProducts = _catalog.where((product) => _cart.containsKey(product.id)).toList();

    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Text(
          'Queue-free self checkout',
          style: Theme.of(context).textTheme.headlineMedium,
        ),
        const SizedBox(height: 10),
        Text(
          'Customers can scan items as they shop, review a live basket, and pay digitally without going to a cashier counter.',
          style: Theme.of(context).textTheme.bodyLarge,
        ),
        const SizedBox(height: 20),
        const InfoBanner(
          title: 'Live scan-to-pay demo',
          subtitle:
              'This interface simulates barcode scanning, dynamic cart updates, and digital checkout.',
          icon: Icons.qr_code_scanner_outlined,
          color: AppTheme.accent,
        ),
        const SizedBox(height: 16),
        SectionCard(
          title: 'Quick scan catalog',
          subtitle: 'Tap any item below to simulate barcode scanning.',
          icon: Icons.document_scanner_outlined,
          accent: AppTheme.accent,
          child: _isLoading
              ? const LinearProgressIndicator()
              : Column(
                  children: _catalog
                      .map(
                        (product) => _CatalogTile(
                          product: product,
                          quantity: _cart[product.id] ?? 0,
                          onScan: () => _scanProduct(product),
                        ),
                      )
                      .toList(),
                ),
        ),
        const SizedBox(height: 16),
        SectionCard(
          title: 'Digital cart',
          subtitle: 'The running basket updates instantly after each scan.',
          icon: Icons.shopping_cart_checkout_outlined,
          accent: AppTheme.primary,
          child: cartProducts.isEmpty
              ? const _EmptyCart()
              : Column(
                  children: [
                    ...cartProducts.map(
                      (product) => _CartTile(
                        product: product,
                        quantity: _cart[product.id] ?? 0,
                        onAdd: () => _changeQuantity(product, 1),
                        onRemove: () => _changeQuantity(product, -1),
                      ),
                    ),
                    const SizedBox(height: 12),
                    _BillRow(
                      label: 'Subtotal',
                      value: 'Rs ${_subtotal.toStringAsFixed(0)}',
                    ),
                    _BillRow(
                      label: 'Service fee',
                      value: 'Rs ${_serviceFee.toStringAsFixed(0)}',
                    ),
                    _BillRow(
                      label: 'Total',
                      value: 'Rs ${_total.toStringAsFixed(0)}',
                      emphasize: true,
                    ),
                  ],
                ),
        ),
        const SizedBox(height: 16),
        SectionCard(
          title: 'Payment and risk monitoring',
          subtitle: 'Choose a payment method and review safety signals.',
          icon: Icons.account_balance_wallet_outlined,
          accent: AppTheme.secondary,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Wrap(
                spacing: 10,
                runSpacing: 10,
                children: _paymentMethods
                    .map(
                      (method) => ChoiceChip(
                        label: Text(method),
                        selected: _selectedPaymentMethod == method,
                        onSelected: (_) {
                          setState(() {
                            _selectedPaymentMethod = method;
                          });
                        },
                      ),
                    )
                    .toList(),
              ),
              const SizedBox(height: 16),
              const _SignalRow(label: 'Repeated rescans', value: 'Tracked'),
              const _SignalRow(label: 'Failed payments', value: 'Tracked'),
              const _SignalRow(label: 'Payment latency spikes', value: 'Tracked'),
              const _SignalRow(label: 'Scan failure rate', value: 'Tracked'),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: _checkout,
                  icon: const Icon(Icons.lock_outline_rounded),
                  label: Text('Pay Rs ${_total.toStringAsFixed(0)}'),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _CatalogTile extends StatelessWidget {
  const _CatalogTile({
    required this.product,
    required this.quantity,
    required this.onScan,
  });

  final ScanProduct product;
  final int quantity;
  final VoidCallback onScan;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFF7FAF8),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Container(
            width: 46,
            height: 46,
            decoration: BoxDecoration(
              color: AppTheme.accent.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(Icons.qr_code_2_rounded, color: AppTheme.accent),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(product.name, style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 4),
                Text(
                  '${product.category} • ${product.barcode} • Aisle ${product.aisleId}',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                'Rs ${product.priceNpr.toStringAsFixed(0)}',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              FilledButton.icon(
                onPressed: onScan,
                icon: const Icon(Icons.add_rounded),
                label: Text(quantity == 0 ? 'Scan' : 'Add'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _CartTile extends StatelessWidget {
  const _CartTile({
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
        color: const Color(0xFFF7FAF8),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(product.name, style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 4),
                Text(
                  'Rs ${product.priceNpr.toStringAsFixed(0)} each',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ],
            ),
          ),
          IconButton(
            onPressed: onRemove,
            icon: const Icon(Icons.remove_circle_outline_rounded),
          ),
          Text(
            '$quantity',
            style: Theme.of(context).textTheme.titleMedium,
          ),
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

class _SignalRow extends StatelessWidget {
  const _SignalRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        children: [
          Expanded(child: Text(label, style: Theme.of(context).textTheme.bodyMedium)),
          Text(
            value,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(fontSize: 14),
          ),
        ],
      ),
    );
  }
}

class _EmptyCart extends StatelessWidget {
  const _EmptyCart();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFFF7FAF8),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        'No items scanned yet. Tap products above to add them to the digital cart.',
        style: Theme.of(context).textTheme.bodyMedium,
      ),
    );
  }
}
