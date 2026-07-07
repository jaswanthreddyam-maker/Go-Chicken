import re
import os

with open('src/app/page.js', 'r', encoding='utf-8') as f:
    code = f.read()

local_vars = [
    't', 'MOCK_AI_FORECAST', 'MOCK_SALES_DATA', 'MOCK_SCATTER_DATA',
    'activeTab', 'setActiveTab', 'currentTime', 'showNotifications', 'setShowNotifications',
    'showPaymentModal', 'setShowPaymentModal', 'searchQuery', 'setSearchQuery',
    'showAddTruckModal', 'setShowAddTruckModal', 'showSplash', 'fadeSplash',
    'showMobileMenu', 'setShowMobileMenu', 'showRefreshVideo', 'setShowRefreshVideo',
    'ordersList', 'setOrdersList', 'productPrices', 'setProductPrices',
    'trucks', 'setTrucks', 'retailers', 'setRetailers',
    'isLoadingOrders', 'isLoadingPrices', 'isLoadingTrucks',
    'ordersError', 'pricesError', 'trucksError',
    'editingPrice', 'setEditingPrice', 'priceSuccessMsg', 'setPriceSuccessMsg',
    'toasts', 'setToasts', 'pollTimer',
    'totalOutstanding', 'totalCapacity', 'activeAlerts', 'sortedOrders',
    'handleStatusChange', 'handlePriceUpdate', 'handleRecordPayment', 'handleAddTruck', 'handleLogout', 'fetchAll'
]

imports = '''"use client";
import React from 'react';
import { 
  ResponsiveContainer, LineChart, CartesianGrid, XAxis, YAxis, Tooltip as RechartsTooltip, Legend, Line, 
  ScatterChart, Scatter, ZAxis
} from 'recharts';
import { 
  BrainCircuit, Truck, AlertTriangle, Wallet, MapPin, Thermometer, 
  Package, Search, Clock, FileText, ChevronRight, CheckCircle2, MoreHorizontal,
  ChevronUp, ChevronDown
} from 'lucide-react';
import { Card, StatBox, TableSkeleton, ChartSkeleton } from '@/components/ui';

'''

def extract_and_create(name, regex_pattern, dest_file):
    global code
    m = re.search(regex_pattern, code, re.DOTALL)
    if not m:
        print(f'{name} not found')
        return None
    
    jsx = m.group(1)
    
    # Find which local variables are used in the JSX
    used_vars = []
    for var in local_vars:
        if re.search(r'\b' + var + r'\b', jsx):
            used_vars.append(var)
    
    props_str = ', '.join(used_vars)
    
    comp_code = f'{imports}\nexport function {name}({{ {props_str} }}) {{\n  return (\n{jsx}\n  );\n}}\n'
    
    with open(dest_file, 'w', encoding='utf-8') as f:
        f.write(comp_code)
    print(f'Created {dest_file} with props: {props_str}')
    
    # Replace the old function in page.js with just returning the component
    prop_passing = ' '.join([f'{v}={{{v}}}' for v in used_vars])
    new_func = f'const render{name.replace("Tab", "")} = () => (\n    <{name} {prop_passing} />\n  );'
    code = code.replace(m.group(0), new_func)
    return True

extract_and_create('OverviewTab', r'const renderOverview = \(\) => \((.*?)\n  \);', 'src/components/dashboard/OverviewTab.js')
extract_and_create('OrdersTab', r'const renderOrders = \(\) => \((.*?)\n  \);', 'src/components/dashboard/OrdersTab.js')
extract_and_create('KhataTab', r'const renderKhata = \(\) => \((.*?)\n  \);', 'src/components/dashboard/KhataTab.js')
extract_and_create('AITab', r'const renderAI = \(\) => \((.*?)\n  \);', 'src/components/dashboard/AITab.js')

import_stmts = '''import { OverviewTab } from '@/components/dashboard/OverviewTab';
import { OrdersTab } from '@/components/dashboard/OrdersTab';
import { KhataTab } from '@/components/dashboard/KhataTab';
import { AITab } from '@/components/dashboard/AITab';
'''
code = code.replace('import { Card, StatBox, Toast, TableSkeleton, ChartSkeleton, classifyError } from \'@/components/ui\';', 
                    'import { Card, StatBox, Toast, TableSkeleton, ChartSkeleton, classifyError } from \'@/components/ui\';\n' + import_stmts)

with open('src/app/page.js', 'w', encoding='utf-8') as f:
    f.write(code)

print('Done extracting dashboard tabs.')
