import 'package:flutter/material.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/info_banner.dart';
import '../../../../core/widgets/section_card.dart';
import '../../data/repositories/scan_to_pay_repository_impl.dart';
import '../../domain/entities/scan_product.dart';
import 'cart_page.dart';
import 'live_scanner_page.dart';
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

  Future<void> _openLiveScanner() async {
    final result = await Navigator.of(context).push<String>(
      MaterialPageRoute<String>(builder: (_) => const LiveScannerPage()),
    );

    if (!mounted || result == null || result.trim().isEmpty) {
      return;
    }

    final normalized = result.trim();
    final matchedProduct = _catalog.cast<ScanProduct?>().firstWhere(
      (product) => product != null && product.barcode == normalized,
      orElse: () => null,
    );

    if (matchedProduct == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Barcode $normalized not found in demo catalog'),
        ),
      );
      return;
    }

    _scanProduct(matchedProduct);
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

  Future<void> _openCart() async {
    final cartProducts = _catalog
        .where((product) => _cart.containsKey(product.id))
        .toList();

    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => StatefulBuilder(
          builder: (context, setModalState) => CartPage(
            products: cartProducts,
            quantities: _cart,
            selectedPaymentMethod: _selectedPaymentMethod,
            onAdd: (product) {
              _changeQuantity(product, 1);
              setModalState(() {});
            },
            onRemove: (product) {
              _changeQuantity(product, -1);
              setModalState(() {});
            },
            onSelectPaymentMethod: (method) {
              setState(() {
                _selectedPaymentMethod = method;
              });
              setModalState(() {});
            },
            onCheckout: _checkout,
          ),
        ),
      ),
    );

    if (mounted) {
      setState(() {});
    }
  }

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
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Container(
          padding: const EdgeInsets.all(22),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFFD97706), Color(0xFF14532D)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(24),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: const [
              Text(
                'Queue-free self checkout',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w700,
                  color: Colors.white,
                ),
              ),
              SizedBox(height: 10),
              Text(
                'Customers can scan items as they shop, review a live basket, and pay digitally without going to a cashier counter.',
                style: TextStyle(
                  fontSize: 14,
                  color: Color(0xFFFFF3E6),
                  height: 1.45,
                ),
              ),
            ],
          ),
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
        _CartSummaryBanner(
          itemCount: _itemCount,
          total: _total,
          onViewCart: _openCart,
        ),
        const SizedBox(height: 16),
        SectionCard(
          title: 'Live barcode scanner',
          subtitle:
              'Use the camera to scan a real barcode and add the product instantly.',
          icon: Icons.center_focus_strong_outlined,
          accent: AppTheme.primary,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Demo barcodes in this app: 890145001118, 890145000001, 890145000003, 890145000062, 890145000210, 890145000314',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: _openLiveScanner,
                  icon: const Icon(Icons.camera_alt_rounded),
                  label: const Text('Open live scanner'),
                ),
              ),
            ],
          ),
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
          title: 'Payment and risk monitoring',
          subtitle: 'Choose a payment method and review safety signals.',
          icon: Icons.account_balance_wallet_outlined,
          accent: AppTheme.secondary,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const _SignalRow(label: 'Repeated rescans', value: 'Tracked'),
              const _SignalRow(label: 'Failed payments', value: 'Tracked'),
              const _SignalRow(
                label: 'Payment latency spikes',
                value: 'Tracked',
              ),
              const _SignalRow(label: 'Scan failure rate', value: 'Tracked'),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: _openCart,
                  icon: const Icon(Icons.shopping_cart_checkout_rounded),
                  label: const Text('Open cart and checkout'),
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
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFDCE5DF)),
      ),
      child: Row(
        children: [
          Container(
            width: 46,
            height: 46,
            decoration: BoxDecoration(
              color: AppTheme.accent.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(14),
            ),
            child: const Icon(Icons.qr_code_2_rounded, color: AppTheme.accent),
          ),
          const SizedBox(width: 12),
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

class _CartSummaryBanner extends StatelessWidget {
  const _CartSummaryBanner({
    required this.itemCount,
    required this.total,
    required this.onViewCart,
  });

  final int itemCount;
  final double total;
  final VoidCallback onViewCart;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF102A1A), Color(0xFF14532D)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(14),
            ),
            child: const Icon(Icons.shopping_cart_rounded, color: Colors.white),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Your cart',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  itemCount == 0
                      ? 'No items added yet'
                      : '$itemCount item${itemCount == 1 ? '' : 's'} • Rs ${total.toStringAsFixed(0)}',
                  style: const TextStyle(
                    color: Color(0xFFD7E7DD),
                    fontSize: 13,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          FilledButton(
            onPressed: onViewCart,
            style: FilledButton.styleFrom(
              backgroundColor: Colors.white,
              foregroundColor: const Color(0xFF102A1A),
            ),
            child: const Text('View cart'),
          ),
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
          Expanded(
            child: Text(label, style: Theme.of(context).textTheme.bodyMedium),
          ),
          Text(
            value,
            style: Theme.of(
              context,
            ).textTheme.titleMedium?.copyWith(fontSize: 14),
          ),
        ],
      ),
    );
  }
}
