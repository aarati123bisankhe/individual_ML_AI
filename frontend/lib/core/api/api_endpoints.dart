import 'package:flutter/foundation.dart';

class ApiEndpoints {
  static const String _webBaseUrl = 'http://127.0.0.1:8000';
  static const String _androidEmulatorBaseUrl = 'http://10.0.2.2:8000';
  static const String _appleSimulatorBaseUrl = 'http://127.0.0.1:8000';
  static const String _fallbackLocalNetworkBaseUrl = 'http://172.25.0.199:8000';

  static String get baseUrl {
    const override = String.fromEnvironment('API_BASE_URL');
    if (override.isNotEmpty) {
      return override;
    }

    if (kIsWeb) {
      return _webBaseUrl;
    }

    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
        return _androidEmulatorBaseUrl;
      case TargetPlatform.iOS:
      case TargetPlatform.macOS:
        return _appleSimulatorBaseUrl;
      default:
        return _fallbackLocalNetworkBaseUrl;
    }
  }

  static String get navigationSearch => '$baseUrl/api/navigation/search';
  static String get inventoryDemand => '$baseUrl/api/inventory/demand';
  static String get customerSegment => '$baseUrl/api/models/customer-segment';
  static String get scanRisk => '$baseUrl/api/models/scan-risk';
  static String get dashboardSummary => '$baseUrl/api/dashboard/summary';
}
