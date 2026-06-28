import 'package:flutter/material.dart';

import '../features/dashboard/presentation/pages/dashboard_page.dart';
import '../features/inventory/presentation/pages/inventory_page.dart';
import '../features/navigation/presentation/pages/navigation_page.dart';
import '../features/scan_to_pay/presentation/pages/payment_confirmation_page.dart';
import '../features/scan_to_pay/presentation/pages/scan_to_pay_page.dart';
import '../features/shell/presentation/pages/main_shell_page.dart';
import '../features/splash/presentation/pages/splash_page.dart';

class AppRoutes {
  static const splash = '/';
  static const shell = '/shell';
  static const navigation = '/navigation';
  static const scanToPay = '/scan-to-pay';
  static const paymentConfirmation = '/scan-to-pay/confirmation';
  static const inventory = '/inventory';
  static const dashboard = '/dashboard';
}

class AppRouter {
  static Route<dynamic> generateRoute(RouteSettings settings) {
    switch (settings.name) {
      case AppRoutes.splash:
        return MaterialPageRoute<void>(builder: (_) => const SplashPage());
      case AppRoutes.shell:
        return MaterialPageRoute<void>(builder: (_) => const MainShellPage());
      case AppRoutes.navigation:
        return MaterialPageRoute<void>(builder: (_) => const NavigationPage());
      case AppRoutes.scanToPay:
        return MaterialPageRoute<void>(builder: (_) => const ScanToPayPage());
      case AppRoutes.paymentConfirmation:
        return MaterialPageRoute<void>(
          builder: (_) => const PaymentConfirmationPage(
            paymentMethod: 'eSewa',
            totalAmount: 0,
            itemCount: 0,
          ),
        );
      case AppRoutes.inventory:
        return MaterialPageRoute<void>(builder: (_) => const InventoryPage());
      case AppRoutes.dashboard:
        return MaterialPageRoute<void>(builder: (_) => const DashboardPage());
      default:
        return MaterialPageRoute<void>(builder: (_) => const SplashPage());
    }
  }
}
