# DMF Configuration Summary

## Provenance
- Tool Version: 0.1.0
- Template Bundle: 8.8
- Workbook Schema: 1.0
- Target DMF Version: 8.8
- Generated: 2026-03-17T14:32:01
- Input Hash: 8a57053531f76b9409f24c787a3be1173429e17f028958c30578045fd7165060
- Findings Summary: 0 errors, 0 warnings

## Controllers
- controller-a (active)
- controller-b (standby)

## Switches by Role
- leaf-delivery-1: delivery
- leaf-filter-1: filter
- leaf-filter-2: filter

## Interfaces and Groups
- leaf-delivery-1:ethernet10 (delivery)
- leaf-delivery-1:ethernet11 (delivery)
- leaf-filter-1:ethernet1 (filter)
- leaf-filter-1:ethernet2 (filter)
- leaf-filter-2:ethernet1 (filter)
- group branch-ingress: 3 members
- group security-tools: 2 members

## Policies
| Name | Priority | Filter | Delivery | Action | Match Rules |
| --- | --- | --- | --- | --- | --- |
| branch-to-ids | 100 | branch-ingress | leaf-delivery-1:ethernet10 | forward | 2 |
| branch-to-recorder | 200 | branch-ingress | leaf-delivery-1:ethernet11 | forward | 1 |

## Fabric Settings
- Fabric Name: fabric-hq

## Operator Attention Required
- None
