import io
try:
    import yaml
    yaml.safe_load(io.open('.github/workflows/campagne.yml', encoding='utf-8'))
    print('YAML OK')
except ImportError:
    print('pyyaml absent, verification par indentation ignoree')
except Exception as e:
    print('YAML ERREUR:', e)
