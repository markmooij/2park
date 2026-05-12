# DOM Reference — 2Park Dashboard

**Generated:** 2026-05-12
**Source:** mijn.2park.nl
**Screenshot:** /tmp/dashboard_dom_audit.png

## Summary

This document contains the actual DOM structure of the 2Park dashboard as
captured during a live session. Use these selectors for automation scripts.

---

## Login Flow

- **Email field selector:** `#login_email`

- **Password field selector:** `#login_password`

- **Submit button selector:** `button[type="submit"]`

- **Post-login URL:** `https://mijn.2park.nl/`


## Dashboard Navigation

- **Dashboard URL:** `https://mijn.2park.nl/`


## Tab Navigation

- **'Lopend' tab tag:** `div`

- **'Lopend' tab text:** `Lopend1
Gepland`

- **'Lopend' tab class:** `tabs-container`


## Booking Card Structure

- **Body classes:** ``


### Selector Match Results

- `.parkapp-item` → 1 matches

- `[class*='parkapp']` → 1 matches

- `[class*='parking']` → 2 matches

- `[class*='item']` → 6 matches


- **Main container:** `div` class=``


- **Main container:** `div` class=`container`


- **Main container:** `main` class=``


- **Main container:** `div` class=`site-content site-list-content`


- **Main container:** `div` class=`site-content-width`


- **Main container:** `div` class=`item-with-settings-content`


- **Main container:** `div` class=`button-menu-content`


- **Main container:** `div` class=`container`


### Tab Container Structure


```

├── div > .tabs-container | Lopend1
Gepland
│   ├── div > .tabs | Lopend1
Gepland
│   │   ├── button > .active | Lopend1
│   │   │   ├── span > .tabText | Lopend
│   │   │   ├── span > .items-count | 1
│   │   ├── button | Gepland
│   │   │   ├── span > .tabText | Gepland

```


```

├── div > .tabs | Lopend1
Gepland
│   ├── button > .active | Lopend1
│   │   ├── span > .tabText | Lopend
│   │   ├── span > .items-count | 1
│   ├── button | Gepland
│   │   ├── span > .tabText | Gepland

```


```

├── span > .tabText | Lopend

```


```

├── span > .tabText | Gepland

```


### Booking Card Details


---

**Card 1**

- **Tag:** `span`

- **Class:** `items-count`

- **Text preview:** 1


**Element tree:**

```

├── span > .items-count | 1
```


---

**Card 2**

- **Tag:** `div`

- **Class:** `item-with-settings-container-default parkapp-item `

- **Text preview:** (Onbekend) | 51PXPN | 14:38,  | vandaag | 23:59,  | vandaag | € 0,34 | Verleng | Stop


**Element tree:**

```

├── div > .item-with-settings-container-default.parkapp-item | (Onbekend)
51PXPN
14:38, 
vandaag
23:59, 
vandaag
€ 0,34
Verleng
Stop
│   ├── div > .item-with-settings-content | (Onbekend)
51PXPN
14:38, 
vandaag
23:59, 
vandaag
€ 0,34
Verleng
Stop
│   │   ├── div > .parkingActionContainer | (Onbekend)
51PXPN
14:38, 
vandaag
23:59, 
vandaag
€ 0,34
│   │   │   ├── div > .favorite-container | (Onbekend)
│   │   │   │   ├── div > .favorite-name | (Onbekend)
│   │   │   ├── div > .license-plate-container | 51PXPN
│   │   │   │   ├── div > .license-plate-block | 51PXPN
│   │   │   ├── div > .timeStartEnd-container | 14:38, 
vandaag
23:59, 
vandaag
│   │   │   │   ├── div > .timeStartEnd-clocks
│   │   │   │   ├── div > .time-container | 14:38, 
vandaag
23:59, 
vandaag
│   │   │   ├── div > .parking-action-balance | € 0,34
│   │   ├── div > .button-menu-container | Verleng
Stop
│   │   │   ├── div > .button-menu-content | Verleng
Stop
│   │   │   │   ├── div > .button-menu-item | Verleng
│   │   │   │   ├── div > .button-menu-item | Stop
│   ├── div > .item-with-settings-button
```


---

**Card 3**

- **Tag:** `div`

- **Class:** `item-with-settings-content`

- **Text preview:** (Onbekend) | 51PXPN | 14:38,  | vandaag | 23:59,  | vandaag | € 0,34 | Verleng | Stop


**Element tree:**

```

├── div > .item-with-settings-content | (Onbekend)
51PXPN
14:38, 
vandaag
23:59, 
vandaag
€ 0,34
Verleng
Stop
│   ├── div > .parkingActionContainer | (Onbekend)
51PXPN
14:38, 
vandaag
23:59, 
vandaag
€ 0,34
│   │   ├── div > .favorite-container | (Onbekend)
│   │   │   ├── div > .favorite-name | (Onbekend)
│   │   │   │   ├── span > .anonymouse | (Onbekend)
│   │   ├── div > .license-plate-container | 51PXPN
│   │   │   ├── div > .license-plate-block | 51PXPN
│   │   │   │   ├── div > .license-plate.active | 51PXPN
│   │   ├── div > .timeStartEnd-container | 14:38, 
vandaag
23:59, 
vandaag
│   │   │   ├── div > .timeStartEnd-clocks
│   │   │   │   ├── div > .dots
│   │   │   │   ├── div > .dots
│   │   │   │   ├── div > .dots
│   │   │   │   ├── div > .dots
│   │   │   │   ├── div > .dots
│   │   │   ├── div > .time-container | 14:38, 
vandaag
23:59, 
vandaag
│   │   │   │   ├── div > .time | 14:38, 
vandaag
│   │   │   │   ├── div > .time | 23:59, 
vandaag
│   │   ├── div > .parking-action-balance | € 0,34
│   ├── div > .button-menu-container | Verleng
Stop
│   │   ├── div > .button-menu-content | Verleng
Stop
│   │   │   ├── div > .button-menu-item | Verleng
│   │   │   │   ├── button > .extend-context-menu-button | Verleng
│   │   │   ├── div > .button-menu-item | Stop
│   │   │   │   ├── button > .stop-context-menu-button | Stop
```


---

**Card 4**

- **Tag:** `div`

- **Class:** `button-menu-item`

- **Text preview:** Verleng


**Element tree:**

```

├── div > .button-menu-item | Verleng
│   ├── button > .extend-context-menu-button | Verleng
```


---

**Card 5**

- **Tag:** `div`

- **Class:** `button-menu-item`

- **Text preview:** Stop


**Element tree:**

```

├── div > .button-menu-item | Stop
│   ├── button > .stop-context-menu-button | Stop
```


## All Buttons on Dashboard


**Total buttons found:** 6


### Button 1

- **Tag:** `button`

- **Text:** `MENU`

- **Class:** `menu-button`

- **Aria-label:** `Menu`



### Button 2

- **Tag:** `button`

- **Text:** `Lopend1`

- **Class:** `active`

- **Aria-label:** `Lopend`



### Button 3

- **Tag:** `button`

- **Text:** `Gepland`

- **Class:** ``

- **Aria-label:** `Gepland`



### Button 4

- **Tag:** `button`

- **Text:** `Verleng`

- **Class:** `extend-context-menu-button`

- **Aria-label:** `Verleng`



### Button 5

- **Tag:** `button`

- **Text:** `Stop`

- **Class:** `stop-context-menu-button`

- **Aria-label:** `Stop`



### Button 6

- **Tag:** `button`

- **Text:** `+
Nieuwe parkeeractie`

- **Class:** ``

- **Aria-label:** `Nieuwe parkeeractie`




## 'Gepland' (Scheduled) Tab

- **'Gepland' tab tag:** `div`

- **'Gepland' tab text:** `Lopend1
Gepland`

- **'Gepland' tab class:** `tabs-container`


### Gepland Tab Content

- **Cards under Gepland:** 6

  - Card class: `items-count`, text: 1

  - Card class: `item-with-settings-container-default parkapp-item `, text: (Onbekend) | 51PXPN | 14:38,  | vandaag | 23:59,  | vandaag | € 0,34 | Verleng | Stop


## All Unique Class Names on Page


**Total unique classes:** 59


```
- `Toastify`
- `active`
- `add-new-button`
- `amount`
- `anonymouse`
- `app`
- `balance`
- `balance-container`
- `balance-label`
- `button-menu-container`
- `button-menu-content`
- `button-menu-item`
- `container`
- `cross`
- `dots`
- `extend-context-menu-button`
- `favorite-container`
- `favorite-name`
- `header-city-block`
- `item-with-settings-button`
- `item-with-settings-container-default`
- `item-with-settings-content`
- `items-count`
- `license-plate`
- `license-plate-block`
- `license-plate-container`
- `license-plate-text`
- `list-container`
- `main-container`
- `main-menu-block`
- `main-menu-container`
- `menu-button`
- `municipality-product-area-theme-and-language-container`
- `page-action-area`
- `page-header-title`
- `page-municipality-product-area`
- `page-municipality-product-row`
- `parkapp-item`
- `parking-action-balance`
- `parkingActionContainer`
- `product-city-block`
- `product-description`
- `product-name`
- `screen-container`
- `screen-fixed-footer`
- `site-content`
- `site-content-width`
- `site-footer`
- `site-list-content`
- `stop-context-menu-button`
- `tabText`
- `tabs`
- `tabs-container`
- `text-menu`
- `theme-default`
- `time`
- `time-container`
- `timeStartEnd-clocks`
- `timeStartEnd-container`
```


## All ID Attributes on Page


**Total elements with IDs:** 2


```
- `div#root ()`
- `div#site-content-scroll (site-content site-list-content)`
```
