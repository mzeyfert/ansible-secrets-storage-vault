import os
from testinfra.utils.ansible_runner import AnsibleRunner

testinfra_hosts = AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('vault')

def test_root_login_to_vault(host):
    vault_root_token = host.file("/root/.vault_root_token").content_string
    cmd = host.run(f'vault login {vault_root_token}')
    assert cmd.rc == 0

def test_create_add_path(host):
    cmd = host.run('vault secrets enable -path=molecule_secrets kv')
    assert cmd.rc == 0

def test_create_kv(host):
    cmd = host.run('vault kv put -mount=molecule_secrets stage login=login pass=pass')
    assert cmd.rc == 0

def test_enable_userpass(host):
    cmd = host.run('vault auth enable userpass')

def test_create_user(host):
    test_policy = (
        '<<EOF\n'
        'path "molecule_secrets/*" {\n'
        '\tcapabilities = ["read", "list", "update"]\n'
        '}\n'
        'EOF'
    )
    create_policy = host.run(f'vault policy write test_policy - {test_policy}')
    add_user = host.run('vault write auth/userpass/users/test_user password=test_password policies=test_policy')
    assert create_policy.rc == 0
    assert add_user.rc == 0

def test_userpass_login(host):
    template = (
        '==== Data ====\n'
        'Key      Value\n'
        '---      -----\n'
        'login    login\n'
        'pass     pass\n'
    )
    login = host.run('vault login -method=userpass username=test_user password=test_password')
    secrets = host.run('vault kv get -mount=molecule_secrets stage')
    assert login.rc == 0
    assert secrets.rc == 0
    assert secrets.stdout == template
