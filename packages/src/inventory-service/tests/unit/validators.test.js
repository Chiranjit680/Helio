// Unit tests placeholder
// Add your unit tests here

const { validateItemData, validateTransactionData } = require('../../src/utils/validators');

describe('Validators', () => {
  describe('validateItemData', () => {
    it('should validate correct item data', () => {
      const data = {
        sku: 'SKU001',
        name: 'Test Item',
        category: 'Electronics',
        quantity: 10,
        unit_price: 99.99,
      };

      const result = validateItemData(data);
      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should reject item without SKU', () => {
      const data = {
        name: 'Test Item',
        category: 'Electronics',
      };

      const result = validateItemData(data);
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('SKU is required');
    });

    it('should reject negative quantity', () => {
      const data = {
        sku: 'SKU001',
        name: 'Test Item',
        category: 'Electronics',
        quantity: -5,
      };

      const result = validateItemData(data);
      expect(result.isValid).toBe(false);
    });
  });

  describe('validateTransactionData', () => {
    it('should validate correct transaction data', () => {
      const data = {
        item_id: '123e4567-e89b-12d3-a456-426614174000',
        type: 'IN',
        quantity: 10,
      };

      const result = validateTransactionData(data);
      expect(result.isValid).toBe(true);
    });

    it('should reject invalid transaction type', () => {
      const data = {
        item_id: '123e4567-e89b-12d3-a456-426614174000',
        type: 'INVALID',
        quantity: 10,
      };

      const result = validateTransactionData(data);
      expect(result.isValid).toBe(false);
    });
  });
});
