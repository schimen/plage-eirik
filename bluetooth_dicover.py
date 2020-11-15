import bluetooth

if __name__ == '__main__':
    print('checking for nearby devices')
    nearby_devices = bluetooth.discover_devices(duration=8, lookup_names=True,
                                                flush_cache=True, lookup_class=False)

    print(f'found {len(nearby_devices)} devices')

    for address, name in nearby_devices:
        try:
            print(f'address: {address}, name: {name}')
        except UnicodeEncodeError:
            print(f'address: {address}, name: {name.encode("utf-8", "replace")} (unicode error)')
