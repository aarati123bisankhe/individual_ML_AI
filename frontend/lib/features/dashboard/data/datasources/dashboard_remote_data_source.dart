import '../../../../core/api/api_endpoints.dart';
import '../../../../core/network/api_client.dart';
import '../models/dashboard_summary_model.dart';

class DashboardRemoteDataSource {
  DashboardRemoteDataSource({ApiClient? client})
    : _client = client ?? const ApiClient();

  final ApiClient _client;

  Future<DashboardSummaryModel> getSummary() async {
    final response = await _client.getMap(
      Uri.parse(ApiEndpoints.dashboardSummary),
    );
    return DashboardSummaryModel.fromJson(response);
  }
}
