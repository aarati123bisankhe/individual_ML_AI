import '../models/scan_product_model.dart';

class ScanCatalogDataSource {
  Future<List<ScanProductModel>> getDemoProducts() async {
    return const [
      ScanProductModel(
        id: 'P000118',
        barcode: '890145001118',
        name: 'DDC Milk 1L',
        category: 'Dairy',
        priceNpr: 103,
        aisleId: 'A0005',
      ),
      ScanProductModel(
        id: 'P000001',
        barcode: '890145000001',
        name: 'Beaten Rice (Chiura) 1kg',
        category: 'Staples',
        priceNpr: 142,
        aisleId: 'A0008',
      ),
      ScanProductModel(
        id: 'P000003',
        barcode: '890145000003',
        name: 'Frozen Momo (Buff) 30pc',
        category: 'Frozen',
        priceNpr: 322,
        aisleId: 'A0006',
      ),
      ScanProductModel(
        id: 'P000062',
        barcode: '890145000062',
        name: 'Dairy Milk 50g',
        category: 'Confectionery',
        priceNpr: 115,
        aisleId: 'A0015',
      ),
      ScanProductModel(
        id: 'P000210',
        barcode: '890145000210',
        name: 'Wai Wai Noodles 75g',
        category: 'Snacks',
        priceNpr: 25,
        aisleId: 'A0011',
      ),
      ScanProductModel(
        id: 'P000314',
        barcode: '890145000314',
        name: 'Sunlight Detergent 1kg',
        category: 'Household',
        priceNpr: 240,
        aisleId: 'A0019',
      ),
    ];
  }
}
