import re

path = r'd:\Go Chicken\backend\alembic\versions\d5b16e54ad00_add_preferred_language.py'
with open(path, 'r') as f:
    c = f.read()

up_idx = c.find('def upgrade() -> None:')
down_idx = c.find('def downgrade() -> None:')

upgrade_body = c[up_idx:down_idx]
downgrade_body = c[down_idx:]

new_upgrade_body = upgrade_body.replace('def upgrade() -> None:', 'def upgrade() -> None:\n    bind = op.get_bind()\n    from sqlalchemy import inspect\n    tables = inspect(bind).get_table_names()\n')

def repl_create(m):
    table = m.group(1)
    body = m.group(0)
    lines = body.split('\n')
    lines[0] = '        ' + lines[0]
    for i in range(1, len(lines)):
        lines[i] = '    ' + lines[i]
    indented_body = '\n'.join(lines)
    return f"    if '{table}' not in tables:\n{indented_body}"

new_upgrade_body = re.sub(r"    op\.create_table\('([^']+)'(?:.*?)(?=\n    op\.|\n\Z)", repl_create, new_upgrade_body, flags=re.DOTALL)

def repl_index(m):
    body = m.group(0)
    table_match = re.search(r"op\.create_index\([^,]+,\s*'([^']+)'", body)
    if not table_match:
        return body
    table = table_match.group(1)
    lines = body.split('\n')
    lines[0] = '        ' + lines[0]
    for i in range(1, len(lines)):
        lines[i] = '    ' + lines[i]
    indented_body = '\n'.join(lines)
    return f"    if '{table}' not in tables:\n{indented_body}"

new_upgrade_body = re.sub(r"    op\.create_index\(.*?(?=\n    op\.|\n\Z)", repl_index, new_upgrade_body, flags=re.DOTALL)

def repl_drop(m):
    table = m.group(1)
    body = m.group(0)
    lines = body.split('\n')
    lines[0] = '        ' + lines[0]
    for i in range(1, len(lines)):
        lines[i] = '    ' + lines[i]
    indented_body = '\n'.join(lines)
    return f"    if '{table}' in tables:\n{indented_body}"

new_upgrade_body = re.sub(r"    op\.drop_table\('([^']+)'\)", repl_drop, new_upgrade_body)

with open('fix_out.py', 'w') as f:
    f.write(c[:up_idx] + new_upgrade_body + downgrade_body)
