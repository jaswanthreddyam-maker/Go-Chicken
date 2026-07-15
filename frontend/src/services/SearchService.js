/**
 * SearchService
 * Manages fuzzy query searching across routes, live data records (Orders, Khata, Fleet),
 * and global action commands.
 */
const SearchService = {
  // Navigation elements
  navigation: [
    { type: 'nav', title: 'Go to Overview', path: 'overview', description: 'Dashboard overview and charts' },
    { type: 'nav', title: 'Go to Orders & Pricing', path: 'orders', description: 'Active orders and live rate cards' },
    { type: 'nav', title: 'Go to Quotes & Pricing', path: 'quotes', description: 'Active quotes and price resolver' },
    { type: 'nav', title: 'Go to Inventory', path: 'inventory', description: 'Warehouse stock snapshot and ledger' },
    { type: 'nav', title: 'Go to IoT Fleet', path: 'fleet', description: 'IoT temperature fleet map' },
    { type: 'nav', title: 'Go to Retailer Khata', path: 'khata', description: 'Retailer credits and outstanding balances' },
    { type: 'nav', title: 'Go to AI Forecasting', path: 'ai', description: 'Ollama demand predictions' },
  ],

  // Actions
  actions: [
    { type: 'action', title: 'Record Payment', actionId: 'record_payment', description: 'Log a payment from a retailer' },
    { type: 'action', title: 'Add Truck', actionId: 'add_truck', description: 'Register a new delivery vehicle' },
    { type: 'action', title: 'Refresh Dashboard', actionId: 'refresh_dashboard', description: 'Trigger synchronization with server' },
  ],

  query(q, { orders = [], retailers = [], trucks = [], quotes = [] } = {}) {
    if (!q) return [];
    const queryStr = q.toLowerCase().trim();

    const matches = [];

    // 1. Search navigation & actions
    this.navigation.forEach(item => {
      if (item.title.toLowerCase().includes(queryStr) || item.description.toLowerCase().includes(queryStr)) {
        matches.push(item);
      }
    });

    this.actions.forEach(item => {
      if (item.title.toLowerCase().includes(queryStr) || item.description.toLowerCase().includes(queryStr)) {
        matches.push(item);
      }
    });

    // 2. Search Orders
    orders.forEach(order => {
      const orderId = String(order.id || '').toLowerCase();
      const phone = String(order.phone_number || '').toLowerCase();
      const item = String(order.item_type || '').toLowerCase();
      if (orderId.includes(queryStr) || phone.includes(queryStr) || item.includes(queryStr)) {
        matches.push({
          type: 'record',
          category: 'Order',
          title: `Order #${orderId.slice(0, 8)} (${order.quantity_kg}kg ${order.item_type})`,
          description: `Status: ${order.status.toUpperCase()} · Customer: ${order.phone_number || 'Manual'}`,
          record: order,
          tab: 'orders'
        });
      }
    });

    // 3. Search Retailers (Khata)
    retailers.forEach(r => {
      const name = String(r.name || r.shopName || '').toLowerCase();
      const phone = String(r.phone || '').toLowerCase();
      const id = String(r.id || '').toLowerCase();
      if (name.includes(queryStr) || phone.includes(queryStr) || id.includes(queryStr)) {
        matches.push({
          type: 'record',
          category: 'Retailer',
          title: `${r.name || r.shopName || 'Retailer'}`,
          description: `Retailer ID: ${r.id} · Phone: ${r.phone} · Balance: ₹${(r.balance || 0).toLocaleString()}`,
          record: r,
          tab: 'khata'
        });
      }
    });

    // 4. Search Trucks
    trucks.forEach(t => {
      const plate = String(t.license_plate || t.plate || '').toLowerCase();
      const devId = String(t.iot_device_id || t.id || '').toLowerCase();
      if (plate.includes(queryStr) || devId.includes(queryStr)) {
        matches.push({
          type: 'record',
          category: 'Truck',
          title: `Truck ${t.license_plate || t.plate}`,
          description: `IoT ID: ${t.iot_device_id || t.id} · Capacity: ${t.max_capacity_kg || t.capacity} kg`,
          record: t,
          tab: 'fleet'
        });
      }
    });

    // 5. Search Quotes
    quotes.forEach(quote => {
      const qNum = String(quote.quote_number || '').toLowerCase();
      const status = String(quote.status || '').toLowerCase();
      if (qNum.includes(queryStr) || status.includes(queryStr)) {
        matches.push({
          type: 'record',
          category: 'Quote',
          title: `Quote ${quote.quote_number}`,
          description: `Total: ₹${Number(quote.total_amount).toLocaleString()} · Status: ${quote.status}`,
          record: quote,
          tab: 'quotes'
        });
      }
    });

    return matches.slice(0, 10); // return top 10 matches
  }
};

export default SearchService;
