import sys

path = r'd:\Go Chicken\backend\alembic\versions\d5b16e54ad00_add_preferred_language.py'
with open(path, 'r') as f:
    lines = f.readlines()

new_lines = []
skip_mode = False
for line in lines:
    # Upgrade block 1
    if "op.create_table('analytics_event_processed'" in line:
        skip_mode = True
    elif "op.create_table('conversation_state'" in line:
        skip_mode = False
        
    # Upgrade block 2
    if "op.drop_table('inventory')" in line:
        skip_mode = True
    elif "op.create_index('ix_comm_kpi_tenant_date'" in line:
        skip_mode = False

    # Downgrade block
    if "op.drop_table('khata_ledger')" in line or \
       "op.drop_table('khata_invoice')" in line or \
       "op.drop_table('customer_balance_projection')" in line or \
       "op.drop_table('analytics_event_processed')" in line or \
       "op.drop_table('pricing_history')" in line:
        new_lines.append("# " + line)
        continue
    
    if "op.drop_index(" in line and ("'khata_" in line or "'analytics_event_processed" in line or "'customer_balance_projection" in line or "'pricing_history" in line):
        new_lines.append("# " + line)
        continue

    # Downgrade re-creations
    if "op.create_table('khata_ledgers'" in line:
        skip_mode = True
    elif "op.drop_index('ix_conv_state_user'" in line:
        skip_mode = False

    if skip_mode:
        new_lines.append("# " + line)
    else:
        new_lines.append(line)

with open(path, 'w') as f:
    f.writelines(new_lines)
