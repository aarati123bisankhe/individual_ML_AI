import 'dart:convert';

import 'package:http/http.dart' as http;

class ApiClient {
  const ApiClient();

  Future<Map<String, dynamic>> getMap(Uri uri) async {
    final response = await http.get(uri);
    if (response.statusCode != 200) {
      throw Exception('Request failed with status ${response.statusCode}');
    }
    return jsonDecode(response.body) as Map<String, dynamic>;
  }
}
