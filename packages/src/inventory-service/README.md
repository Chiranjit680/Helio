# Inventory Service

A microservice for managing inventory, stock transactions, and alerts built with Express.js and PostgreSQL.

## Features

- **Item Management**: CRUD operations for inventory items
- **Stock Transactions**: Track stock movements (IN, OUT, ADJUSTMENT)
- **Alerts**: Automated low stock and critical stock alerts
- **Analytics**: Inventory overview, stock levels, movement trends

## Prerequisites

- Node.js >= 18.0.0
- PostgreSQL >= 13
- npm or yarn

## Installation

1. Clone the repository
2. Navigate to the inventory-service directory:
   ```bash
   cd packages/src/inventory-service
   ```

3. Install dependencies:
   ```bash
   npm install
   ```

4. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```

5. Update the `.env` file with your database credentials

6. Run database migrations:
   ```bash
   psql -U postgres -d inventory_db -f migrations/001_create_inventory_items.sql
   psql -U postgres -d inventory_db -f migrations/002_create_transactions.sql
   psql -U postgres -d inventory_db -f migrations/003_create_alerts.sql
   ```

## Running the Service

### Development
```bash
npm run dev
```

### Production
```bash
npm start
```

The service will start on port 3001 (or the port specified in `.env`).

## API Endpoints

### Health Check
- `GET /api/inventory/health` - Service health status

### Items
- `GET /api/inventory/items` - Get all items (paginated)
- `GET /api/inventory/items/:id` - Get item by ID
- `POST /api/inventory/items` - Create new item
- `PUT /api/inventory/items/:id` - Update item
- `DELETE /api/inventory/items/:id` - Delete item
- `PATCH /api/inventory/items/:id/stock` - Update stock quantity

### Transactions
- `GET /api/inventory/transactions` - Get all transactions
- `GET /api/inventory/transactions/:id` - Get transaction by ID
- `POST /api/inventory/transactions` - Create transaction
- `GET /api/inventory/transactions/item/:itemId` - Get transactions for item
- `GET /api/inventory/transactions/type/:type` - Get transactions by type

### Alerts
- `GET /api/inventory/alerts` - Get all alerts
- `GET /api/inventory/alerts/:id` - Get alert by ID
- `POST /api/inventory/alerts` - Create alert
- `PUT /api/inventory/alerts/:id` - Update alert
- `DELETE /api/inventory/alerts/:id` - Delete alert
- `PATCH /api/inventory/alerts/:id/acknowledge` - Acknowledge alert
- `GET /api/inventory/alerts/active` - Get active alerts

### Analytics
- `GET /api/inventory/analytics/overview` - Inventory overview
- `GET /api/inventory/analytics/stock-levels` - Stock level distribution
- `GET /api/inventory/analytics/movement` - Stock movement trends
- `GET /api/inventory/analytics/top-items` - Top items by volume
- `GET /api/inventory/analytics/low-stock` - Low stock items
- `GET /api/inventory/analytics/value` - Inventory value

## Project Structure

```
inventory-service/
├── src/
│   ├── config/          # Configuration files
│   ├── routes/          # API route definitions
│   ├── controllers/     # Request handlers
│   ├── services/        # Business logic
│   ├── models/          # Database queries
│   ├── middleware/      # Express middleware
│   ├── utils/           # Utility functions
│   └── app.js           # Express app setup
├── migrations/          # Database migrations
├── tests/               # Test files
├── server.js            # Entry point
└── package.json
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| PORT | Server port | 3001 |
| NODE_ENV | Environment | development |
| DB_HOST | PostgreSQL host | localhost |
| DB_PORT | PostgreSQL port | 5432 |
| DB_NAME | Database name | inventory_db |
| DB_USER | Database user | postgres |
| DB_PASSWORD | Database password | - |
| JWT_SECRET | JWT signing secret | - |
| LOW_STOCK_THRESHOLD | Low stock alert threshold | 10 |
| CRITICAL_STOCK_THRESHOLD | Critical stock threshold | 5 |

## Testing

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

## License

ISC
