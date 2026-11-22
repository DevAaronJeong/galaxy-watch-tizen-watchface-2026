# Watch trust store (Galaxy Watch SM-R805N, Tizen 5.5.0.2)

Root certificates by trust domain, read from `/usr/share/ca-certificates/fingerprint/fingerprint_list.xml` and `fingerprint_list_ext.xml` on the watch. File names refer to `/usr/share/ca-certificates/tizen/`.

A root listed under `tizen-revoked` is rejected even if it also appears in another domain.

## Author signatures: `tizen-developer`

| Root | File | Status |
| --- | --- | --- |
| Tizen Developers Root Class | `Tizen_Developers_Root_Class.pem` | Trusted (root of Samsung author certificates) |
| GEAR2 SDK AUTHOR Root Class | `author_eng_root.pem` | Trusted |
| Tizen Developers Root | `tizen-developers-root.pem` | **Revoked** (root of the Tizen Studio default author certificate) |
| Tizen Test Developer Root CA | `tizen-developer-root-ca.pem` | **Revoked** |

## Distributor signatures, public level

| Root | File | Domains | Status |
| --- | --- | --- | --- |
| GEAR2 PROD Public Root Class | `gear_prod_public.pem` | public, store | Trusted (Galaxy Store) |
| GEAR2 Test Public Root Class | `gear_verify_public.pem` | public, verify | Trusted |
| GEAR2 DEVELOPER Public Root Class | `gear_test_public.pem` | public, test | Trusted (developer, device ID checked) |
| Samsung Tizen Public Root Class | `tizen_samsung_public_root.pem` | public | Trusted |
| Samsung Tizen DEVELOPER Public Root Class | `samsung_tizen_dev_public.pem` | public, test | Trusted (developer, device ID checked) |
| Tizen Store Public Root Class | `tizen_store_public.pem` | public, store | Trusted |
| Tizen Store TEST Public Root Class | `tizen_store_test_public.pem` | public, verify | Trusted |
| Tizen Association DEVELOPER Public Root Class | `tizen_association_dev_public.pem` | public, test | Trusted |
| Public Class Developer Root | `tizen-public-class-developer-root.pem` | public, revoked | **Revoked** |
| Tizen Public Distributor Root CA | `tizen-distributor-root-ca-public.pem` | public, revoked | **Revoked** (root of the old Tizen Studio default distributor certificate) |

## Partner and platform levels

The partner and platform counterparts of `tizen_store_*`, `tizen_association_dev_*`, `tizen_samsung_*_root`, `samsung_tizen_dev_*`, `gear_verify_*`, `gear_test_*` and `gear_prod_*` are trusted. `tizen-partner-class-developer-root`, `tizen-platform-class-developer-root` and `tizen-distributor-root-ca-partner*` are revoked.

## Not present at all

| Root | Where it comes from |
| --- | --- |
| **VD DEVELOPER Public Root Class** | Distributor certificates issued by Samsung Certificate Manager as of November 2026 |
| Tizen Studio Public Root Class | The newer Tizen Studio default distributor certificate (`tizen-distributor-signer-new`) |

## Verify on your watch

```bash
sdb connect <watch-ip>:26101
sdb shell cat /usr/share/ca-certificates/fingerprint/fingerprint_list.xml
sdb shell cat /usr/share/ca-certificates/fingerprint/fingerprint_list_ext.xml
sdb pull /usr/share/ca-certificates ./watch-ca
```

Or run [`tools/check_signature_trust.py`](../tools/check_signature_trust.py) against a package.
