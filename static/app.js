// TechTailor Catalog Data
const CATALOG = {
    men: [
        {
            id: 'silver-slate',
            name: 'Silver Slate Suit Set',
            code: 'VI_D 963/1',
            price: 32000,
            priceStrike: 40000,
            desc: 'This premium light grey checkered suit features a bespoke tailored silhouette. Crafted from premium superfine tropical wool, it is paired with a matching checkered tie and designed for year-round versatility.',
            details: '• Standard 2-Button Single Breasted Jacket<br>• Notch Lapel with Flower Loop<br>• Flat Front Trousers with Side Adjusters<br>• 100% Merino Wool, 260 GSM<br>• Soft Slate check weave pattern',
            packaging: 'Delivered in premium sustainable garment bags, complete with a heavy-duty wooden hanger and individual dust covers.',
            image: '/static/assets/suit_silver_slate_1781719754640.jpg'
        },
        {
            id: 'pearl-white',
            name: 'Pearl White Suit Set',
            code: 'VI_D 964/2',
            price: 35000,
            priceStrike: 45000,
            desc: 'An exquisite double-breasted suit set crafted in pearl white, designed for weddings and high-profile evening events. Made from a premium cashmere-wool blend.',
            details: '• 6-Button Double Breasted Jacket<br>• Peak Lapels with Gold Boutonniere Details<br>• Slim-Fit Trousers with Satin Waistband<br>• 90% Merino Wool, 10% Cashmere<br>• Premium satin lining',
            packaging: 'Hand-packed in bespoke hard-shell storage boxes with protective tissue lining to retain crisp lapel rolls.',
            image: '' // Fallback styled by CSS
        },
        {
            id: 'umber-pinstripe',
            name: 'Umber Pinstripe Suit Set',
            code: 'VI_D 967/5',
            price: 38000,
            priceStrike: 48000,
            desc: 'A striking power suit featuring vertical chalk pinstripes on a warm umber brown backdrop. Ideal for the discerning executive who values classic tailoring heritage.',
            details: '• 3-Piece suit set with matching vest<br>• 2-Button Jacket, Peak Lapels<br>• Pinstripe alignment across pockets<br>• English Wool Flannel, 280 GSM',
            packaging: 'Delivered in premium breathable canvas suit carriers with dedicated zipper pockets for ties and cufflinks.',
            image: ''
        },
        {
            id: 'soot-black',
            name: 'Soot Black Tuxedo Set',
            code: 'VI_D 962/9',
            price: 34000,
            priceStrike: 42000,
            desc: 'The ultimate evening wear. Crafted in pure soot black, this tuxedo features silk satin lapels and buttons, providing an unparalleled fit for formal sundowners or receptions.',
            details: '• 1-Button Shawl Collar Tuxedo Jacket<br>• Silk Satin Lapels, Pocket Piping & Buttons<br>• Trousers with Satin Side Stripes<br>• 120s Wool Crepe, 250 GSM',
            packaging: 'Delivered in luxury custom garment carriers with custom internal suit-shield padding.',
            image: ''
        }
    ],
    women: [
        {
            id: 'misty-aqua',
            name: 'Misty Aqua Suit Set',
            code: 'VI_W 502/1',
            price: 31000,
            priceStrike: 39000,
            desc: 'A modern pastel pantsuit designed for the contemporary woman. Features a relaxed yet structured fit in a serene misty aqua hue, perfect for day events.',
            details: '• Single-button longline jacket<br>• Wide-leg trousers with high waist<br>• Lightweight breathable wool-crepe blend<br>• Full interior cupro lining',
            packaging: 'Delivered on contoured premium hangers in custom women-suit boxes.',
            image: ''
        },
        {
            id: 'charcoal-blazer',
            name: 'Charcoal Dusk Blazer',
            code: 'VI_W 504/4',
            price: 18000,
            priceStrike: 24000,
            desc: 'An essential structured double-breasted blazer. Crafted from textured hopsack wool, it functions as a versatile standalone or outer piece for semi-formal styling.',
            details: '• Fitted double-breasted silhouette<br>• Structured shoulders and slim lapels<br>• Metallic silver buttons<br>• Side flap pockets',
            packaging: 'Packaged in tissue wraps inside custom dust protection sleeves.',
            image: ''
        }
    ],
    accessories: [
        {
            id: 'printed-tie-combo',
            name: 'Printed Tie & Pocket Square Combo',
            price: 1800,
            priceStrike: 2500,
            desc: 'A matching necktie and pocket square combo made from 100% printed mulberry silk. Features classic geometric paisley patterns.',
            details: '• 3.25" Wide Jacquard Silk Tie<br>• 12"x12" Pocket Square with hand-rolled edges<br>• 100% Mulberry Silk',
            packaging: 'Delivered in a velvet-lined wooden presentation box.',
            image: ''
        },
        {
            id: 'mens-belt',
            name: 'Classic Men\'s Leather Belt',
            price: 2000,
            priceStrike: 2850,
            desc: 'A premium full-grain calfskin leather belt with a brushed nickel buckle. Reversible design with soot black on one side and umber brown on the other.',
            details: '• Reversible strap (Black / Brown)<br>• Full-grain vegetable-tanned leather<br>• Width: 35mm',
            packaging: 'Delivered inside a custom velvet drawstring protective pouch.',
            image: ''
        }
    ]
};

// Application State
let state = {
    activePage: 'home',
    activeProductId: null,
    cart: [],
    activeWorkflow: {
        id: '',
        title: '',
        bucket: '',
        summary: ''
    },
    customization: {
        height: '',
        bodyType: '',
        sizeMethod: 'ready', // 'ready' | 'custom'
        readyJacketSize: 'EU 50 | INTERNATIONAL M | UK/US 40',
        readyTrouserSize: 'EU 42 | INTERNATIONAL M | UK/US 32',
        customMeasurements: {
            bust: '',
            waist: '',
            hips: '',
            upper: '',
            neck: '',
            outerArm: '',
            shoulder: '',
            length: '',
            width: '',
            neckPoint: '',
            crotch: '',
            cuff: '',
            lowerHips: '',
            thigh: '',
            lowerLength: ''
        },
        fitting: 'regular_fit',
        selectedFabricType: 'same', // 'same' | 'catalog' | 'own'
        selectedCatalogFabric: 'D 963/1 - Suit Soft stone'
    },
    appointment: {
        city: '',
        date: ''
    },
    chatHistory: [],
    groqApiKey: '',
    sessionId: ''
};

// ==========================================================================
// INITIALIZATION
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
    const savedSessionId = localStorage.getItem('tt_session_id');
    if (savedSessionId) {
        state.sessionId = savedSessionId;
    } else {
        state.sessionId = (typeof crypto !== 'undefined' && crypto.randomUUID)
            ? crypto.randomUUID()
            : `tt-${Date.now()}-${Math.random().toString(16).slice(2)}`;
        localStorage.setItem('tt_session_id', state.sessionId);
    }

    // Load API Key from local storage if available
    const savedKey = localStorage.getItem('groq_api_key');
    if (savedKey) {
        state.groqApiKey = savedKey;
        document.getElementById('groq-api-key-input').value = savedKey;
        updateApiKeyUI(true);
    } else {
        // Check if server environment has key
        checkServerApiKey();
    }

    updateWorkflowUI({});
    navigateTo('home');
    updateCartUI();
});

// Check if server already has Groq Key configured
async function checkServerApiKey() {
    try {
        const response = await fetch('/api/config');
        const data = await response.json();
        if (data.groq_api_key_configured) {
            updateApiKeyUI(true, "Env Configured");
        }
    } catch (e) {
        console.error("Failed to fetch server config status", e);
    }
}

// ==========================================================================
// NAVIGATION & RENDERING
// ==========================================================================
function navigateTo(page, productId = null) {
    state.activePage = page;
    state.activeProductId = productId;

    // Update active nav link
    document.querySelectorAll('.main-nav li').forEach(el => el.classList.remove('active'));
    const navEl = document.getElementById(`nav-${page}`);
    if (navEl) navEl.classList.add('active');

    // Close all drawers
    toggleDrawer('custom-drawer', false);
    toggleDrawer('fabric-drawer', false);
    toggleDrawer('cart-drawer', false);

    renderPage();
}

function selectProduct(productId) {
    // Find the product in catalog
    let foundProduct = null;
    let category = null;
    for (const [cat, items] of Object.entries(CATALOG)) {
        foundProduct = items.find(p => p.id === productId);
        if (foundProduct) {
            category = cat;
            break;
        }
    }

    if (foundProduct) {
        navigateTo('detail', productId);
    }
}

function renderPage() {
    const pageContent = document.getElementById('page-content');
    
    if (state.activePage === 'home') {
        pageContent.innerHTML = `
            <!-- Hero Banner -->
            <div class="hero-section" style="background-image: url('/static/assets/hero_banner_1781719717923.jpg')">
                <div class="hero-overlay"></div>
                <div class="hero-content">
                    <p class="text-secondary" style="letter-spacing: 0.15em; font-weight: 500; font-size: 0.8rem; text-transform: uppercase;">Bespoke Tailoring Meets Tech Precision</p>
                    <h1>BESPOKE SUITS,<br>CRAFTED FOR YOU.</h1>
                    <p>Experience precision fitting through doorstep technician measurements or ready-made templates. Handcrafted by master artisans with materials curated globally.</p>
                    <div class="hero-actions-row">
                        <button class="btn btn-gold" onclick="navigateTo('men')">Browse Men</button>
                        <button class="btn btn-dark" onclick="navigateTo('women')">Browse Women</button>
                    </div>
                </div>
            </div>

            <!-- Features -->
            <div class="features-grid">
                <div class="feature-card">
                    <i class="fa-solid fa-tape feature-icon"></i>
                    <h3>Doorstep Tailor Service</h3>
                    <p>Our expert technicians visit your home to take 20+ measurement checkpoints and show fabrics in Bangalore, Mumbai, and Gurgaon.</p>
                </div>
                <div class="feature-card">
                    <i class="fa-solid fa-scissors feature-icon"></i>
                    <h3>Custom Fabric Catalog</h3>
                    <p>Select from hundreds of Italian and English wools, linens, and silks, or opt to "Use Your Own Fabric" for personalized convenience.</p>
                </div>
                <div class="feature-card">
                    <i class="fa-solid fa-award feature-icon"></i>
                    <h3>Premium Craftsmanship</h3>
                    <p>Every jacket is half-canvassed by default to mold perfectly to your chest frame over time. Premium trims and stitches guaranteed.</p>
                </div>
            </div>
        `;
    } else if (state.activePage === 'men' || state.activePage === 'women' || state.activePage === 'accessories') {
        const titleMap = { 'men': "Men's Custom Attire", 'women': "Women's Custom Attire", 'accessories': "Luxury Accessories" };
        const subtitleMap = { 'men': "Suits, Jackets, Shirts & Trousers", 'women': "Bespoke Pantsuits, Blazers & Trousers", 'accessories': "Handmade Silk Ties, Leather Belts & Scarves" };
        
        const items = CATALOG[state.activePage];
        let itemsHtml = '';

        items.forEach(product => {
            const hasImage = !!product.image;
            const fallbackLetter = product.name[0];
            const bgClass = product.id === 'soot-black' ? 'bg-soot' : (product.id === 'pearl-white' ? 'bg-pearl' : 'bg-umber');
            
            itemsHtml += `
                <div class="product-card" onclick="selectProduct('${product.id}')">
                    <div class="product-image-container">
                        ${hasImage ? 
                            `<img src="${product.image}" alt="${product.name}">` : 
                            `<div class="product-image-fallback ${bgClass}">
                                <i class="fa-solid fa-user-tie"></i>
                                <span>${fallbackLetter}</span>
                             </div>`
                        }
                    </div>
                    <div class="product-info">
                        <span class="text-xs text-muted" style="letter-spacing: 0.05em; text-transform: uppercase;">${product.code || 'ACCESSORY'}</span>
                        <h3 class="product-title">${product.name}</h3>
                        <div class="product-price-row">
                            <span class="price-actual">₹ ${product.price.toLocaleString()}</span>
                            ${product.priceStrike ? `<span class="price-strike">₹ ${product.priceStrike.toLocaleString()}</span>` : ''}
                        </div>
                    </div>
                </div>
            `;
        });

        pageContent.innerHTML = `
            <div class="catalog-banner">
                <h2>${titleMap[state.activePage]}</h2>
                <p>${subtitleMap[state.activePage]}</p>
            </div>
            
            <!-- Category Filter Tabs -->
            <div class="filter-tabs">
                <button class="filter-tab active">ALL</button>
                <button class="filter-tab">FORMAL WEAR</button>
                <button class="filter-tab">WEDDING & CEREMONIAL</button>
                <button class="filter-tab">SEMI-FORMAL</button>
            </div>

            <div class="products-grid">
                ${itemsHtml}
            </div>
        `;
    } else if (state.activePage === 'detail') {
        let product = null;
        for (const items of Object.values(CATALOG)) {
            product = items.find(p => p.id === state.activeProductId);
            if (product) break;
        }

        if (!product) {
            pageContent.innerHTML = `<h3>Product not found</h3>`;
            return;
        }

        const hasImage = !!product.image;
        const bgClass = product.id === 'soot-black' ? 'bg-soot' : (product.id === 'pearl-white' ? 'bg-pearl' : 'bg-umber');
        const isAccessory = !product.code;

        // Custom details accordion depending on product
        pageContent.innerHTML = `
            <div class="product-detail-container">
                <div class="product-gallery">
                    ${hasImage ? 
                        `<img src="${product.image}" alt="${product.name}">` : 
                        `<div class="product-gallery-fallback ${bgClass}">
                            <i class="fa-solid fa-user-tie" style="font-size: 5rem;"></i>
                         </div>`
                    }
                </div>
                <div class="product-specs">
                    <span class="specs-id">${product.code || 'ACCESSORY'}</span>
                    <h1 class="specs-title">${product.name}</h1>
                    <div class="specs-price">
                        <span>₹ ${product.price.toLocaleString()}</span>
                        ${product.priceStrike ? `<span class="price-strike" style="font-size: 1.1rem; margin-left: 10px;">₹ ${product.priceStrike.toLocaleString()}</span>` : ''}
                    </div>
                    
                    <p class="text-sm text-muted" style="line-height: 1.6; margin-bottom: 2rem;">
                        ${product.desc}
                    </p>

                    <div class="specs-actions">
                        ${isAccessory ? 
                            `<button class="btn btn-gold w-full" onclick="addAccessoryToCart('${product.id}')">Add To Bag</button>` :
                            `
                            <button class="btn btn-gold" style="flex: 1;" onclick="openCustomizerDrawer()">Customize & Size</button>
                            <button class="btn btn-dark" onclick="openFabricDrawer()"><i class="fa-solid fa-palette" style="margin-right: 6px;"></i> Fabrics</button>
                            `
                        }
                    </div>

                    <!-- Accordion Info -->
                    <div class="accordion-item active" id="accordion-desc">
                        <div class="accordion-header" onclick="toggleAccordion('accordion-desc')">
                            <span>STYLE DETAILS</span>
                            <i class="fa-solid fa-chevron-down"></i>
                        </div>
                        <div class="accordion-body">
                            <p>${product.details}</p>
                        </div>
                    </div>

                    <div class="accordion-item" id="accordion-pack">
                        <div class="accordion-header" onclick="toggleAccordion('accordion-pack')">
                            <span>PACKAGING & DELIVERY</span>
                            <i class="fa-solid fa-chevron-down"></i>
                        </div>
                        <div class="accordion-body">
                            <p>${product.packaging}</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}

// Accordion helper
function toggleAccordion(id) {
    const item = document.getElementById(id);
    item.classList.toggle('active');
    
    // Rotate chevron
    const chevron = item.querySelector('.fa-chevron-down');
    if (chevron) {
        chevron.style.transform = item.classList.contains('active') ? 'rotate(180deg)' : 'rotate(0deg)';
    }
}

// Drawer toggles
function toggleDrawer(drawerId, isOpen) {
    const drawer = document.getElementById(drawerId);
    const overlay = document.getElementById(`${drawerId}-overlay`);
    if (drawer && overlay) {
        if (isOpen) {
            drawer.classList.add('active');
            overlay.classList.add('active');
        } else {
            drawer.classList.remove('active');
            overlay.classList.remove('active');
        }
    }
}

// Fabric Drawers
function openFabricDrawer() {
    // Populate active status
    const type = state.customization.selectedFabricType;
    document.querySelectorAll('.fabric-option').forEach(el => el.classList.remove('active'));
    
    if (type === 'same') {
        document.getElementById('fabric-same').classList.add('active');
    } else if (type === 'catalog') {
        document.getElementById('fabric-catalog').classList.add('active');
        document.getElementById('catalog-fabric-select').value = state.customization.selectedCatalogFabric;
        updateCatalogFabricColorBox(state.customization.selectedCatalogFabric);
    } else if (type === 'own') {
        document.getElementById('fabric-own').classList.add('active');
    }
    
    toggleDrawer('fabric-drawer', true);
}

function selectFabricOption(type) {
    state.customization.selectedFabricType = type;
    document.querySelectorAll('.fabric-option').forEach(el => el.classList.remove('active'));
    
    if (type === 'same') {
        document.getElementById('fabric-same').classList.add('active');
    } else if (type === 'catalog') {
        document.getElementById('fabric-catalog').classList.add('active');
        const selectVal = document.getElementById('catalog-fabric-select').value;
        state.customization.selectedCatalogFabric = selectVal;
        updateCatalogFabricColorBox(selectVal);
    } else if (type === 'own') {
        document.getElementById('fabric-own').classList.add('active');
    }
}

function updateCatalogFabric(val) {
    state.customization.selectedCatalogFabric = val;
    selectFabricOption('catalog');
}

function updateCatalogFabricColorBox(fabricName) {
    const colorMap = {
        'D 963/1 - Suit Soft stone': '#c6c2b8',
        'AC 103/1 - Suit Pearl': '#eae8e1',
        'AC 103/2 - Suit Navy': '#1c2438',
        'AC 103/8 - Suit Beige': '#dfd2bc',
        'AW 267/3 - Jacket Fawn': '#af9881',
        'AW 268/1 - Jacket Cobalt blue': '#1c4c96',
        'CHARCOAL DUSK TWILL - PDW40': '#292d34',
        'D 922/3 - Suit Steal blue': '#4a5b6d',
        'D 936/2 - Suit Burnt maroon': '#6e2b34',
        'D 959/2 - Suit Hunter green': '#2b473a',
        'DRIFTWOOD BEIGE - PDW13': '#af9983',
        'ICY SKY MIST - PDW04': '#b5cbd7',
        'MISTY AQUA - PDW06': '#89b6b5',
        'STEEL SHADOW TWILL - S15': '#5d626a',
        'V 712/11 - Jacket Soft Pink': '#f3d1d5',
        'V 712/12 - Jacket Pistachio': '#c5d9c8',
        'V 712/13 - Jacket Mauve Grey': '#bdafb5',
        'V 712/3 - Bandhgala Burgundy': '#5c1b26',
        'WD 201/2 - Suit Royal blue': '#0a3382',
        'WL 212/1 - Jacket Blush': '#e8c5c1'
    };
    const box = document.getElementById('catalog-fabric-color');
    if (box) {
        box.style.backgroundColor = colorMap[fabricName] || '#6a8d73';
    }
}

function confirmFabricSelection() {
    toggleDrawer('fabric-drawer', false);
    let desc = "Same Fabric";
    if (state.customization.selectedFabricType === 'catalog') {
        desc = `Catalog: ${state.customization.selectedCatalogFabric}`;
    } else if (state.customization.selectedFabricType === 'own') {
        desc = "Customer Fabric";
    }
    
    showToast(`Fabric applied: ${desc}`);
    updateMonitor(`ApplyFabricOption: type=${state.customization.selectedFabricType}, fabric=${state.customization.selectedCatalogFabric}`);
}

// Customizer Drawer
function openCustomizerDrawer() {
    // Populate form elements from state
    document.getElementById('measure-height').value = state.customization.height;
    document.getElementById('measure-body-type').value = state.customization.bodyType;
    selectSizeMethod(state.customization.sizeMethod);
    
    document.getElementById('ready-jacket-size').value = state.customization.readyJacketSize;
    document.getElementById('ready-trouser-size').value = state.customization.readyTrouserSize;
    
    // Custom sizes
    document.getElementById('custom-fitting').value = state.customization.fitting;
    document.getElementById('cust-bust').value = state.customization.customMeasurements.bust;
    document.getElementById('cust-waist').value = state.customization.customMeasurements.waist;
    document.getElementById('cust-hips').value = state.customization.customMeasurements.hips;
    document.getElementById('cust-upper').value = state.customization.customMeasurements.upper;
    document.getElementById('cust-neck').value = state.customization.customMeasurements.neck;
    document.getElementById('cust-outer-arm').value = state.customization.customMeasurements.outerArm;
    document.getElementById('cust-shoulder').value = state.customization.customMeasurements.shoulder;
    document.getElementById('cust-length').value = state.customization.customMeasurements.length;
    document.getElementById('cust-width').value = state.customization.customMeasurements.width;
    document.getElementById('cust-neck-point').value = state.customization.customMeasurements.neckPoint;
    
    document.getElementById('cust-crotch').value = state.customization.customMeasurements.crotch;
    document.getElementById('cust-cuff').value = state.customization.customMeasurements.cuff;
    document.getElementById('cust-lower-hips').value = state.customization.customMeasurements.lowerHips;
    document.getElementById('cust-thigh').value = state.customization.customMeasurements.thigh;
    document.getElementById('cust-lower-length').value = state.customization.customMeasurements.lowerLength;

    // Appointment
    document.getElementById('appt-city').value = state.appointment.city;
    document.getElementById('appt-date').value = state.appointment.date;
    
    if (state.appointment.city || state.appointment.date) {
        expandAppointmentSection(true);
    } else {
        expandAppointmentSection(false);
    }

    validateFormFields();
    toggleDrawer('custom-drawer', true);
}

function selectSizeMethod(method) {
    state.customization.sizeMethod = method;
    document.querySelectorAll('.size-tab').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.size-panel').forEach(el => el.classList.remove('active'));
    
    if (method === 'ready') {
        document.getElementById('tab-ready').classList.add('active');
        document.getElementById('panel-ready').classList.add('active');
    } else {
        document.getElementById('tab-custom').classList.add('active');
        document.getElementById('panel-custom').classList.add('active');
    }
}

// Collapsible Appointment section
let apptExpanded = false;
function toggleAppointmentSection() {
    expandAppointmentSection(!apptExpanded);
}

function expandAppointmentSection(expand) {
    apptExpanded = expand;
    const body = document.getElementById('appointment-body');
    const chevron = document.getElementById('appointment-chevron');
    if (body && chevron) {
        body.style.display = expand ? 'block' : 'none';
        chevron.style.transform = expand ? 'rotate(180deg)' : 'rotate(0deg)';
    }
}

// Validator
function validateFormFields() {
    const height = document.getElementById('measure-height').value;
    const bodyType = document.getElementById('measure-body-type').value;
    const warning = document.getElementById('custom-warning');
    
    if (height && bodyType) {
        warning.style.display = 'none';
        return true;
    }
    return false;
}

// Submit customization & Add to bag
function submitCustomization() {
    const height = document.getElementById('measure-height').value;
    const bodyType = document.getElementById('measure-body-type').value;
    const warning = document.getElementById('custom-warning');
    const warningText = document.getElementById('warning-text');

    if (!height) {
        warningText.innerText = "Oops! Please select a height.";
        warning.style.display = 'flex';
        // Scroll drawer to bottom so warning is visible
        document.getElementById('custom-drawer').querySelector('.drawer-body').scrollTop = 500;
        return;
    }
    
    if (!bodyType) {
        warningText.innerText = "Oops! Please select a body type.";
        warning.style.display = 'flex';
        document.getElementById('custom-drawer').querySelector('.drawer-body').scrollTop = 500;
        return;
    }

    warning.style.display = 'none';

    // Save fields to state
    state.customization.height = height;
    state.customization.bodyType = bodyType;
    state.customization.readyJacketSize = document.getElementById('ready-jacket-size').value;
    state.customization.readyTrouserSize = document.getElementById('ready-trouser-size').value;
    
    state.customization.fitting = document.getElementById('custom-fitting').value;
    state.customization.customMeasurements.bust = document.getElementById('cust-bust').value;
    state.customization.customMeasurements.waist = document.getElementById('cust-waist').value;
    state.customization.customMeasurements.hips = document.getElementById('cust-hips').value;
    state.customization.customMeasurements.upper = document.getElementById('cust-upper').value;
    state.customization.customMeasurements.neck = document.getElementById('cust-neck').value;
    state.customization.customMeasurements.outerArm = document.getElementById('cust-outer-arm').value;
    state.customization.customMeasurements.shoulder = document.getElementById('cust-shoulder').value;
    state.customization.customMeasurements.length = document.getElementById('cust-length').value;
    state.customization.customMeasurements.width = document.getElementById('cust-width').value;
    state.customization.customMeasurements.neckPoint = document.getElementById('cust-neck-point').value;
    
    state.customization.customMeasurements.crotch = document.getElementById('cust-crotch').value;
    state.customization.customMeasurements.cuff = document.getElementById('cust-cuff').value;
    state.customization.customMeasurements.lowerHips = document.getElementById('cust-lower-hips').value;
    state.customization.customMeasurements.thigh = document.getElementById('cust-thigh').value;
    state.customization.customMeasurements.lowerLength = document.getElementById('cust-lower-length').value;

    state.appointment.city = document.getElementById('appt-city').value;
    state.appointment.date = document.getElementById('appt-date').value;

    // Find active product
    let product = null;
    for (const items of Object.values(CATALOG)) {
        product = items.find(p => p.id === state.activeProductId);
        if (product) break;
    }

    if (!product) return;

    // Formulate Cart Item options description
    let optionsText = `Height: ${state.customization.height.toUpperCase()}, Body: ${state.customization.bodyType.toUpperCase()}`;
    if (state.customization.sizeMethod === 'ready') {
        optionsText += `, Jacket: ${state.customization.readyJacketSize}, Trouser: ${state.customization.readyTrouserSize}`;
    } else {
        optionsText += `, Custom (${state.customization.fitting} Fit)`;
    }
    
    // Fabric
    let fabricDesc = "Fabric: Same Pattern";
    if (state.customization.selectedFabricType === 'catalog') {
        fabricDesc = `Fabric: ${state.customization.selectedCatalogFabric}`;
    } else if (state.customization.selectedFabricType === 'own') {
        fabricDesc = "Fabric: Customer Supplied";
    }
    optionsText += ` | ${fabricDesc}`;

    // Technician Appointment
    if (state.appointment.city && state.appointment.date) {
        optionsText += ` | Tech booking: ${state.appointment.city} on ${state.appointment.date}`;
    }

    // Add to cart state
    const cartItem = {
        id: `${product.id}-${Date.now()}`,
        productId: product.id,
        name: product.name,
        price: product.price,
        image: product.image,
        options: optionsText
    };

    state.cart.push(cartItem);
    updateCartUI();
    toggleDrawer('custom-drawer', false);
    
    showToast(`${product.name} added to Bag!`);
    updateMonitor(`AddToCart: item=${product.id}, params=${optionsText}`);
    
    // Automatically open cart for user to review
    toggleDrawer('cart-drawer', true);
}

// Add simple accessory directly to cart without customization drawer
function addAccessoryToCart(productId) {
    let product = null;
    for (const items of Object.values(CATALOG)) {
        product = items.find(p => p.id === productId);
        if (product) break;
    }
    if (!product) return;

    const cartItem = {
        id: `${product.id}-${Date.now()}`,
        productId: product.id,
        name: product.name,
        price: product.price,
        image: product.image,
        options: 'Ready Made Accessory'
    };

    state.cart.push(cartItem);
    updateCartUI();
    showToast(`${product.name} added to Bag!`);
    updateMonitor(`AddToCart: accessory=${product.id}`);
    toggleDrawer('cart-drawer', true);
}

// ==========================================================================
// CART OPERATIONS
// ==========================================================================
function removeFromCart(cartItemId) {
    state.cart = state.cart.filter(item => item.id !== cartItemId);
    updateCartUI();
    showToast("Item removed from Bag.");
    updateMonitor(`RemoveFromCart: id=${cartItemId}`);
}

function updateCartUI() {
    const list = document.getElementById('cart-items-list');
    const badge = document.getElementById('cart-badge-count');
    const emptyMsg = document.getElementById('empty-cart-message');
    const totalsSec = document.getElementById('cart-totals-section');
    
    badge.innerText = state.cart.length;

    if (state.cart.length === 0) {
        emptyMsg.style.display = 'flex';
        totalsSec.style.display = 'none';
        list.innerHTML = '';
        list.appendChild(emptyMsg);
        return;
    }

    emptyMsg.style.display = 'none';
    totalsSec.style.display = 'block';
    
    let html = '';
    let subtotal = 0;
    
    state.cart.forEach(item => {
        subtotal += item.price;
        const hasImage = !!item.image;
        const bgClass = item.productId === 'soot-black' ? 'bg-soot' : (item.productId === 'pearl-white' ? 'bg-pearl' : 'bg-umber');

        html += `
            <div class="cart-item">
                <div class="cart-item-img">
                    ${hasImage ? 
                        `<img src="${item.image}" alt="${item.name}">` : 
                        `<div class="product-image-fallback text-xs ${bgClass}" style="height: 100%;"><i class="fa-solid fa-user-tie"></i></div>`
                    }
                </div>
                <div class="cart-item-details">
                    <span class="cart-item-name">${item.name}</span>
                    <span class="cart-item-options">${item.options}</span>
                    <span class="cart-item-price">₹ ${item.price.toLocaleString()}</span>
                </div>
                <i class="fa-regular fa-trash-can cart-item-remove" onclick="removeFromCart('${item.id}')"></i>
            </div>
        `;
    });

    list.innerHTML = html;

    const gst = Math.round(subtotal * 0.18);
    const total = subtotal + gst;

    document.getElementById('cart-subtotal').innerText = `₹ ${subtotal.toLocaleString()}`;
    document.getElementById('cart-gst').innerText = `₹ ${gst.toLocaleString()}`;
    document.getElementById('cart-total').innerText = `₹ ${total.toLocaleString()}`;
}

function checkoutMock() {
    alert(`Order Placed (Mock Checkout)!\nTotal paid: ${document.getElementById('cart-total').innerText}\nThank you for shopping with TechTailor.`);
    state.cart = [];
    updateCartUI();
    toggleDrawer('cart-drawer', false);
    updateMonitor("CheckoutCompleted: orderStatus=PLACED");
}

// ==========================================================================
// CONCIERGE CHAT LOGIC (AGENT INTEGRATION)
// ==========================================================================
async function sendMessage() {
    const input = document.getElementById('chat-input');
    const query = input.value.trim();
    if (!query) return;

    input.value = '';
    
    // Add user message to UI
    addMessageToChat('user', query);
    state.chatHistory.push({ role: 'user', content: query });

    // Display typing indicator
    const typingId = showTypingIndicator(true);

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Groq-API-Key': state.groqApiKey || ''
            },
            body: JSON.stringify({
                messages: state.chatHistory,
                session_id: state.sessionId
            })
        });

        const data = await response.json();
        
        showTypingIndicator(false, typingId);

        if (data.error) {
            console.error("Agent Engine Error:", data.error);
        }

        updateWorkflowUI(data);

        // Add assistant reply to UI
        const assistantContent = data.error
            ? `${data.response || 'The agent could not complete the request.'}\n\nError: ${data.error}`
            : data.response;
        addMessageToChat('assistant', assistantContent);
        state.chatHistory.push({ role: 'assistant', content: assistantContent });

        // Process any returned structured actions
        if (data.actions && data.actions.length > 0) {
            await processAgentActions(data.actions);
        }

    } catch (e) {
        showTypingIndicator(false, typingId);
        addMessageToChat('assistant', "I apologize, but I'm having trouble connecting to the tailoring concierge service. Please ensure the server is running and check your internet connection.");
        console.error(e);
    }
}

function handleInputKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

function sendSuggestion(text) {
    document.getElementById('chat-input').value = text;
    sendMessage();
}

function addMessageToChat(role, content) {
    const container = document.getElementById('chat-messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role === 'user' ? 'user-msg' : 'assistant-msg'}`;
    
    // Simple markdown parsing to HTML
    let parsedContent = content
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/- (.*?)(<br>|$)/g, '<li>$1</li>');
        
    if (parsedContent.includes('<li>')) {
        // Wrap grouped list items in <ul>
        parsedContent = parsedContent.replace(/(<li>.*?<\/li>)+/g, '<ul>$&</ul>');
    }

    msgDiv.innerHTML = `<div class="message-bubble">${parsedContent}</div>`;
    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
}

function showTypingIndicator(show, existingId = null) {
    const container = document.getElementById('chat-messages');
    if (show) {
        const id = 'typing-' + Date.now();
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message assistant-msg';
        msgDiv.id = id;
        msgDiv.innerHTML = `
            <div class="message-bubble">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        container.appendChild(msgDiv);
        container.scrollTop = container.scrollHeight;
        return id;
    } else if (existingId) {
        const indicator = document.getElementById(existingId);
        if (indicator) indicator.remove();
    }
}

// Toast popup
function showToast(msg) {
    const toast = document.getElementById('toast');
    const toastMsg = document.getElementById('toast-message');
    toastMsg.innerText = msg;
    toast.classList.add('active');
    setTimeout(() => {
        toast.classList.remove('active');
    }, 3000);
}

// Activity monitor log
function updateMonitor(eventText) {
    const body = document.getElementById('tracker-body');
    const firstEvent = body.querySelector('.italic');
    if (firstEvent) firstEvent.remove();
    
    const time = new Date().toLocaleTimeString();
    const div = document.createElement('div');
    div.className = 'tracker-event';
    div.innerHTML = `[${time}] <span style="color:#e5be79">${eventText}</span>`;
    
    body.appendChild(div);
    body.scrollTop = body.scrollHeight;
}

// ==========================================================================
// API KEY CONFIGURATION
// ==========================================================================
function toggleApiKeyInput() {
    document.getElementById('api-key-dropdown').classList.toggle('active');
}

async function saveApiKey() {
    const key = document.getElementById('groq-api-key-input').value.trim();
    if (!key) return;

    state.groqApiKey = key;
    localStorage.setItem('groq_api_key', key);
    updateApiKeyUI(true);
    toggleApiKeyInput();
    
    // Save on backend too (.env setup)
    try {
        await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ groq_api_key: key })
        });
    } catch (e) {
        console.error("Backend config sync failed", e);
    }
    
    showToast("Groq API Key configured!");
}

function updateApiKeyUI(isConfigured, label = "Active Status") {
    const btnText = document.getElementById('key-btn-text');
    const statusText = document.getElementById('status-text');
    
    if (isConfigured) {
        btnText.innerHTML = `<i class="fa-solid fa-check text-green"></i> Key Configured`;
        statusText.innerText = "Active & ready to tailor";
    } else {
        btnText.innerText = "Groq API Key";
        statusText.innerText = "Setup key to enable AI";
    }
}

function updateWorkflowUI(meta) {
    state.activeWorkflow = {
        id: meta?.workflow_id || '',
        title: meta?.workflow_title || 'Master Entry Router',
        bucket: meta?.intent_bucket || 'exploring',
        summary: meta?.workflow_summary || 'Route the visitor into the right TechTailor journey.'
    };

    const workflowTitle = document.getElementById('workflow-title');
    const workflowBucket = document.getElementById('workflow-bucket');
    const workflowSummary = document.getElementById('workflow-summary');
    const workflowId = document.getElementById('workflow-id');

    if (workflowTitle) workflowTitle.innerText = state.activeWorkflow.title;
    if (workflowBucket) workflowBucket.innerText = state.activeWorkflow.bucket.replace(/_/g, ' ');
    if (workflowSummary) workflowSummary.innerText = state.activeWorkflow.summary;
    if (workflowId) workflowId.innerText = state.activeWorkflow.id || 'master_entry';
}

// ==========================================================================
// AGENT ACTION BRIDGE (LLM DRIVES FRONTEND)
// ==========================================================================
async function processAgentActions(actions) {
    for (const action of actions) {
        const { type } = action;
        
        updateMonitor(`ExecutingAction: type=${type}`);
        
        switch (type) {
            case 'navigate':
                if (action.page) {
                    navigateTo(action.page);
                    updateMonitor(`Result: Navigated to page '${action.page}'`);
                }
                break;
                
            case 'select_product':
                if (action.product_id) {
                    selectProduct(action.product_id);
                    updateMonitor(`Result: Selected product '${action.product_id}'`);
                }
                break;
                
            case 'customize_fabric':
                if (action.fabric_type) {
                    selectFabricOption(action.fabric_type);
                    if (action.fabric_type === 'catalog' && action.fabric_name) {
                        const selectEl = document.getElementById('catalog-fabric-select');
                        // Find match in catalog fabric option values
                        for (let opt of selectEl.options) {
                            if (opt.value.toLowerCase().includes(action.fabric_name.toLowerCase())) {
                                selectEl.value = opt.value;
                                updateCatalogFabric(opt.value);
                                break;
                            }
                        }
                    }
                    confirmFabricSelection();
                    updateMonitor(`Result: Customized Fabric type=${action.fabric_type}`);
                }
                break;
                
            case 'customize_measurements':
                // Open Drawer first
                openCustomizerDrawer();
                
                if (action.height) {
                    document.getElementById('measure-height').value = action.height;
                }
                if (action.body_type) {
                    document.getElementById('measure-body-type').value = action.body_type;
                }
                
                // Ready sizes vs Custom measurements selection
                if (action.size_method) {
                    selectSizeMethod(action.size_method);
                    
                    if (action.size_method === 'ready') {
                        if (action.ready_jacket_size) {
                            document.getElementById('ready-jacket-size').value = action.ready_jacket_size;
                        }
                        if (action.ready_trouser_size) {
                            document.getElementById('ready-trouser-size').value = action.ready_trouser_size;
                        }
                    } else if (action.size_method === 'custom') {
                        if (action.fitting) {
                            document.getElementById('custom-fitting').value = action.fitting;
                        }
                        if (action.custom_measurements) {
                            const cm = action.custom_measurements;
                            if (cm.bust) document.getElementById('cust-bust').value = cm.bust;
                            if (cm.waist) document.getElementById('cust-waist').value = cm.waist;
                            if (cm.hips) document.getElementById('cust-hips').value = cm.hips;
                            if (cm.upper) document.getElementById('cust-upper').value = cm.upper;
                            if (cm.neck) document.getElementById('cust-neck').value = cm.neck;
                            if (cm.outer_arm) document.getElementById('cust-outer-arm').value = cm.outer_arm;
                            if (cm.shoulder) document.getElementById('cust-shoulder').value = cm.shoulder;
                            if (cm.length) document.getElementById('cust-length').value = cm.length;
                            if (cm.width) document.getElementById('cust-width').value = cm.width;
                            if (cm.neck_point) document.getElementById('cust-neck-point').value = cm.neck_point;
                            
                            if (cm.crotch) document.getElementById('cust-crotch').value = cm.crotch;
                            if (cm.cuff) document.getElementById('cust-cuff').value = cm.cuff;
                            if (cm.lower_hips) document.getElementById('cust-lower-hips').value = cm.lower_hips;
                            if (cm.thigh) document.getElementById('cust-thigh').value = cm.thigh;
                            if (cm.lower_length) document.getElementById('cust-lower-length').value = cm.lower_length;
                        }
                    }
                }
                
                validateFormFields();
                updateMonitor(`Result: Set height/sizes in drawer`);
                break;
                
            case 'schedule_technician':
                openCustomizerDrawer();
                expandAppointmentSection(true);
                
                if (action.city) {
                    document.getElementById('appt-city').value = action.city;
                }
                if (action.date) {
                    document.getElementById('appt-date').value = action.date;
                }
                updateMonitor(`Result: Configured technician scheduler: city=${action.city}, date=${action.date}`);
                break;
                
            case 'add_to_bag':
                // Wait short moment to let visual state reflect before closing and adding
                await new Promise(resolve => setTimeout(resolve, 600));
                submitCustomization();
                updateMonitor(`Result: Add to Bag completed`);
                break;
                
            case 'open_cart':
                toggleDrawer('cart-drawer', true);
                updateMonitor(`Result: Opened Shopping Cart Drawer`);
                break;

            case 'show_workflow_summary':
                updateMonitor(`Result: Workflow=${action.workflow_id || state.activeWorkflow.id || 'master_entry'}`);
                showToast(`Active workflow: ${state.activeWorkflow.title}`);
                break;

            case 'capture_lead':
                updateMonitor('Result: Lead captured in conversation context');
                showToast('Lead captured for follow-up');
                break;

            case 'show_recommendations':
                updateMonitor('Result: Displayed recommendations context');
                break;

            case 'compare_products':
                updateMonitor('Result: Comparison guidance prepared');
                break;

            case 'request_photo':
                updateMonitor('Result: Requested customer photo');
                break;

            case 'show_style_preview':
                updateMonitor('Result: Prepared style preview flow');
                break;

            case 'set_budget':
                updateMonitor('Result: Budget guidance requested');
                break;

            case 'offer_alternative':
                updateMonitor('Result: Alternative option suggested');
                break;

            case 'show_shipping':
                updateMonitor('Result: Shipping guidance displayed');
                break;

            case 'request_measurements':
                openCustomizerDrawer();
                updateMonitor('Result: Measurement workflow requested');
                break;

            case 'create_quote':
                updateMonitor('Result: Quote request prepared');
                showToast('Quote request prepared');
                break;

            case 'handoff_human':
                updateMonitor('Result: Human handoff requested');
                showToast('Human sales follow-up requested');
                break;

            case 'save_preferences':
                updateMonitor('Result: Preferences saved');
                break;

            case 'start_consultation':
                updateMonitor('Result: Consultation flow started');
                showToast('Consultation requested');
                break;
                
            default:
                console.warn("Unknown agent action:", action);
        }
        
        // Brief sleep between actions to make the transitions visual and clear to the user
        await new Promise(resolve => setTimeout(resolve, 800));
    }
}
