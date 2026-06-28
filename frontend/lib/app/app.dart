import 'package:flutter/material.dart';

import '../core/theme/app_theme.dart';
import 'routes.dart';

class SmartRetailApp extends StatelessWidget {
  const SmartRetailApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Smart Grocery',
      theme: AppTheme.lightTheme,
      initialRoute: AppRoutes.splash,
      onGenerateRoute: AppRouter.generateRoute,
    );
  }
}
