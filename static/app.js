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
            image: 'https://images.unsplash.com/photo-1594938298603-c8148c4dae35?auto=format&fit=crop&w=800&q=80'
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
            image: 'https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=800&q=80'
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
            image: 'https://images.unsplash.com/photo-1598808503746-f34c53b9323e?auto=format&fit=crop&w=800&q=80'
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
            image: 'https://images.unsplash.com/photo-1593030761757-71fae45fa0e7?auto=format&fit=crop&w=800&q=80'
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
            image: 'https://images.unsplash.com/photo-1584273143981-41c073dfe8f8?auto=format&fit=crop&w=800&q=80'
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
            image: 'https://images.unsplash.com/photo-1617137984095-74e4e5e3613f?auto=format&fit=crop&w=800&q=80'
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
            image: 'https://images.unsplash.com/photo-1589756823695-278bc923f962?auto=format&fit=crop&w=800&q=80'
        },
        {
            id: 'mens-belt',
            name: 'Classic Men\'s Leather Belt',
            price: 2000,
            priceStrike: 2850,
            desc: 'A premium full-grain calfskin leather belt with a brushed nickel buckle. Reversible design with soot black on one side and umber brown on the other.',
            details: '• Reversible strap (Black / Brown)<br>• Full-grain vegetable-tanned leather<br>• Width: 35mm',
            packaging: 'Delivered inside a custom velvet drawstring protective pouch.',
            image: 'https://images.unsplash.com/photo-1624222247344-550fb60583dc?auto=format&fit=crop&w=800&q=80'
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
    let height = document.getElementById('measure-height').value || 'regular';
    let bodyType = document.getElementById('measure-body-type').value || 'mesomorph_men';
    
    document.getElementById('measure-height').value = height;
    document.getElementById('measure-body-type').value = bodyType;

    const warning = document.getElementById('custom-warning');
    if (warning) warning.style.display = 'none';

    state.customization.height = height;
    state.customization.bodyType = bodyType;
    state.customization.readyJacketSize = document.getElementById('ready-jacket-size').value;
    state.customization.readyTrouserSize = document.getElementById('ready-trouser-size').value;
    
    state.customization.fitting = document.getElementById('custom-fitting').value;

    let product = null;
    for (const items of Object.values(CATALOG)) {
        product = items.find(p => p.id === state.activeProductId);
        if (product) break;
    }

    if (!product) {
        product = CATALOG.men[0];
    }

    let optionsText = `Height: ${height.toUpperCase()}, Body: ${bodyType.toUpperCase()}`;
    if (state.customization.sizeMethod === 'ready') {
        optionsText += `, Jacket: ${state.customization.readyJacketSize}, Trouser: ${state.customization.readyTrouserSize}`;
    } else {
        optionsText += `, Custom (${state.customization.fitting} Fit)`;
    }
    
    let fabricDesc = "Fabric: Soft Stone Wool";
    if (state.customization.selectedFabricType === 'catalog') {
        fabricDesc = `Fabric: ${state.customization.selectedCatalogFabric}`;
    } else if (state.customization.selectedFabricType === 'own') {
        fabricDesc = "Fabric: Customer Supplied";
    }
    optionsText += ` | ${fabricDesc}`;

    if (state.appointment.city && state.appointment.date) {
        optionsText += ` | Tech booking: ${state.appointment.city} on ${state.appointment.date}`;
    }

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
    
    toggleDrawer('cart-drawer', true);
}

// Add simple accessory directly to cart without customization drawer
function addAccessoryToCart(productId) {
    let product = null;
    for (const items of Object.values(CATALOG)) {
        product = items.find(p => p.id === productId);
        if (product) break;
    }
    if (!product) product = CATALOG.accessories[0];

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
// ==========================================================================
// SPEECH SYNTHESIS ENGINE (AGENT VOICE OUTPUT)
// ==========================================================================
let isMuted = false;

if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    window.speechSynthesis.onvoiceschanged = () => {
        window.speechSynthesis.getVoices();
    };
}

function toggleMute() {
    isMuted = !isMuted;
    const btnText = document.getElementById('tts-btn-text');
    const icon = document.getElementById('tts-icon');
    if (isMuted) {
        if (window.speechSynthesis) window.speechSynthesis.cancel();
        if (btnText) btnText.innerText = "Voice OFF";
        if (icon) icon.className = "fa-solid fa-volume-xmark text-muted";
        showToast("Agent voice muted");
    } else {
        if (btnText) btnText.innerText = "Voice ON";
        if (icon) icon.className = "fa-solid fa-volume-high text-gold";
        showToast("Agent voice enabled");
        speakText("Agent voice enabled. I am ready to guide you.");
    }
}

function speakText(text) {
    if (isMuted || typeof window === 'undefined' || !('speechSynthesis' in window)) return;
    if (!text) return;

    try {
        window.speechSynthesis.cancel();

        let cleanText = text
            .replace(/<[^>]*>/g, ' ')
            .replace(/[*_`#~]/g, '')
            .replace(/https?:\/\/\S+/g, '')
            .replace(/\s+/g, ' ')
            .trim();

        if (!cleanText) return;

        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;

        const voices = window.speechSynthesis.getVoices();
        const preferredVoice = voices.find(v => 
            (v.lang.startsWith('en') && (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Samantha') || v.name.includes('Karen') || v.name.includes('Daniel') || v.name.includes('Arthur')))
        ) || voices.find(v => v.lang.startsWith('en'));

        if (preferredVoice) {
            utterance.voice = preferredVoice;
        }

        window.speechSynthesis.speak(utterance);
    } catch (err) {
        console.error("Speech synthesis error:", err);
    }
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
        addMessageToChat('assistant', assistantContent, data.actions || []);
        state.chatHistory.push({ role: 'assistant', content: assistantContent });

        // Speak the assistant's response so agent is never mute!
        speakText(assistantContent);

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

function quickAddToCart(productId) {
    let foundProduct = null;
    for (const [cat, items] of Object.entries(CATALOG)) {
        foundProduct = items.find(p => p.id === productId);
        if (foundProduct) break;
    }

    if (!foundProduct) {
        foundProduct = CATALOG.men[0];
    }

    const cartItem = {
        id: `${foundProduct.id}-${Date.now()}`,
        productId: foundProduct.id,
        name: foundProduct.name,
        price: foundProduct.price,
        image: foundProduct.image,
        options: `Fabric: ${state.customization.selectedCatalogFabric || 'Soft Stone Wool'} | Sizing: ${state.customization.sizeMethod === 'custom' ? 'Custom Measurement' : 'Ready Size M'}`
    };

    state.cart.push(cartItem);
    updateCartUI();
    showToast(`Added ${foundProduct.name} to Shopping Bag!`);
    speakText(`I have added ${foundProduct.name} to your Shopping Bag.`);
    toggleDrawer('cart-drawer', true);
    updateMonitor(`Result: Added '${foundProduct.name}' to Bag directly from Chat Widget`);
}

function quickCustomizeProduct(productId) {
    selectProduct(productId);
    let foundProduct = null;
    for (const [cat, items] of Object.entries(CATALOG)) {
        foundProduct = items.find(p => p.id === productId);
        if (foundProduct) break;
    }
    const productName = foundProduct ? foundProduct.name : productId;
    sendSuggestion(`I would like to customize options for ${productName}`);
}

function selectFabricFromChat(fabricName) {
    state.customization.selectedFabricType = 'catalog';
    state.customization.selectedCatalogFabric = fabricName;
    confirmFabricSelection();
    showToast(`Fabric selected: ${fabricName}`);
    updateMonitor(`Result: Fabric set to '${fabricName}' from Chat Widget`);
}

function quickScheduleVisit(city) {
    state.appointment.city = city;
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const dateStr = tomorrow.toISOString().split('T')[0];
    state.appointment.date = dateStr;
    const elCity = document.getElementById('appt-city');
    if (elCity) elCity.value = city;
    const elDate = document.getElementById('appt-date');
    if (elDate) elDate.value = dateStr;
    showToast(`Scheduled Technician visit in ${city}!`);
    speakText(`Scheduled technician visit in ${city} for tomorrow.`);
    updateMonitor(`Result: Technician visit set for ${city}`);
}

const STOCK_OPTION_IMAGES = {
    'office formal': '/static/assets/occasion_office.jpg',
    'office': '/static/assets/occasion_office.jpg',
    'wedding reception': '/static/assets/occasion_wedding.jpg',
    'wedding': '/static/assets/occasion_wedding.jpg',
    'casual weekend': '/static/assets/occasion_casual.jpg',
    'casual': '/static/assets/occasion_casual.jpg',
    'party wear': '/static/assets/occasion_party.jpg',
    'party': '/static/assets/occasion_party.jpg',
    'travel / resort': '/static/assets/occasion_travel.jpg',
    'travel': '/static/assets/occasion_travel.jpg',
    'superfine wool': '/static/assets/fabric_soft_stone.jpg',
    'italian cashmere': '/static/assets/fabric_pearl.jpg',
    'summer linen': '/static/assets/fabric_cobalt.jpg',
    'pure cotton': '/static/assets/fabric_burgundy.jpg',
    'view suits': '/static/assets/suit_silver_slate.jpg',
    'view shirts': '/static/assets/suit_pearl_white.jpg',
    'view ethnic wear': '/static/assets/suit_soot_black.jpg',
    'view accessories': '/static/assets/accessory_tie.jpg',
    'slim fit': '/static/assets/suit_silver_slate.jpg',
    'regular fit': '/static/assets/suit_pearl_white.jpg'
};

function findCatalogProduct(productId) {
    for (const items of Object.values(CATALOG)) {
        const match = items.find(x => x.id === productId);
        if (match) return match;
    }
    return null;
}

function addMessageToChat(role, content, actions = []) {
    const container = document.getElementById('chat-messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role === 'user' ? 'user-msg' : 'assistant-msg'}`;
    
    let parsedContent = content
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/- (.*?)(<br>|$)/g, '<li>$1</li>');
        
    if (parsedContent.includes('<li>')) {
        parsedContent = parsedContent.replace(/(<li>.*?<\/li>)+/g, '<ul>$&</ul>');
    }

    let widgetHTML = '';

    if (role === 'assistant') {
        // 1. Interactive Visual Option Cards with Net Stock Images
        const optionsAction = actions.find(a => a.type === 'present_options');
        let optionsList = optionsAction?.options || [];

        if (optionsList.length === 0) {
            if (content.toLowerCase().includes('occasion') || content.toLowerCase().includes('bring you')) {
                optionsList = ['Office Formal', 'Wedding Reception', 'Casual Weekend', 'Party Wear', 'Travel / Resort'];
            } else if (content.toLowerCase().includes('fabric')) {
                optionsList = ['Superfine Wool', 'Italian Cashmere', 'Summer Linen', 'Pure Cotton'];
            } else if (content.toLowerCase().includes('fit') || content.toLowerCase().includes('sizing') || content.toLowerCase().includes('measure')) {
                optionsList = ['Slim Fit', 'Regular Fit', 'Ready Sizing (M/L/XL)', 'Book Doorstep Tailor Visit'];
            } else if (content.toLowerCase().includes('recommend') || content.toLowerCase().includes('look')) {
                optionsList = ['View Suits', 'View Shirts', 'View Ethnic Wear', 'View Accessories'];
            }
        }

        if (optionsList.length > 0) {
            const titleText = optionsAction?.title || 'Choose an option to proceed:';
            widgetHTML += `
                <div class="chat-widget-options">
                    <div class="chat-widget-title"><i class="fa-solid fa-layer-group text-gold"></i> ${titleText}</div>
                    <div class="chat-visual-options-grid">
                        ${optionsList.map(opt => {
                            const key = opt.toLowerCase();
                            const imgUrl = STOCK_OPTION_IMAGES[key] || '/static/assets/suit_silver_slate.jpg';
                            return `
                                <div class="chat-visual-option-card" onclick="sendSuggestion('${opt.replace(/'/g, "\\'")}')">
                                    <div class="chat-visual-option-img" style="background-image: url('${imgUrl}')"></div>
                                    <div class="chat-visual-option-label">${opt}</div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
        }

        // 2. Visual Product Recommendations Cards
        const recAction = actions.find(a => ['show_recommendations', 'compare_products', 'offer_alternative'].includes(a.type));
        let productIds = recAction?.product_ids || [];
        const lowerContent = content.toLowerCase();
        if (productIds.length === 0 && (lowerContent.includes('wedding') || lowerContent.includes('groom'))) {
            productIds = ['pearl-white', 'printed-tie-combo', 'mens-belt'];
        } else if (productIds.length === 0 && (lowerContent.includes('office') || lowerContent.includes('business') || lowerContent.includes('interview'))) {
            productIds = ['silver-slate', 'printed-tie-combo', 'mens-belt'];
        } else if (productIds.length === 0 && (lowerContent.includes('black tie') || lowerContent.includes('tuxedo') || lowerContent.includes('evening'))) {
            productIds = ['soot-black', 'printed-tie-combo', 'mens-belt'];
        } else if (productIds.length === 0 && (lowerContent.includes('recommend') || lowerContent.includes('look') || lowerContent.includes('collection') || lowerContent.includes('suit'))) {
            productIds = ['silver-slate', 'umber-pinstripe', 'printed-tie-combo'];
        }

        if (productIds.length > 0) {
            let cardsHTML = '';
            const bundleItems = Array.isArray(recAction?.bundle_items) ? recAction.bundle_items : [];
            const crossSells = Array.isArray(recAction?.cross_sells) ? recAction.cross_sells : [];
            const recommendationTitle = recAction?.title || 'Recommended outfit combination';
            const recommendationReason = recAction?.reason || '';

            if (recommendationReason) {
                widgetHTML += `
                    <div class="chat-widget-card gold-border">
                        <div class="chat-widget-title"><i class="fa-solid fa-bullseye text-gold"></i> Why this combination works</div>
                        <p class="text-sm" style="line-height: 1.6; margin-top: 6px;">${recommendationReason}</p>
                    </div>
                `;
            }

            if (bundleItems.length > 0) {
                widgetHTML += `
                    <div class="chat-widget-card">
                        <div class="chat-widget-title"><i class="fa-solid fa-layer-group text-gold"></i> ${recommendationTitle}</div>
                        <div class="chat-bundle-strip">
                            ${bundleItems.map(item => {
                                const product = findCatalogProduct(item.product_id);
                                const label = product ? product.name : item.product_id;
                                const role = item.role || 'supporting piece';
                                return `
                                    <div class="chat-bundle-pill">
                                        <strong>${label}</strong>
                                        <span>${role}</span>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    </div>
                `;
            }

            if (crossSells.length > 0) {
                widgetHTML += `
                    <div class="chat-widget-card">
                        <div class="chat-widget-title"><i class="fa-solid fa-bag-shopping text-gold"></i> Matching add-ons</div>
                        <div class="chat-cross-sell-list">
                            ${crossSells.map(item => `<span class="chat-cross-sell-chip">${item}</span>`).join('')}
                        </div>
                    </div>
                `;
            }

            productIds.forEach(id => {
                const p = findCatalogProduct(id);
                if (p) {
                    const bundleMeta = bundleItems.find(item => item.product_id === id);
                    cardsHTML += `
                        <div class="chat-product-card">
                            <div class="chat-product-img">
                                <img src="${p.image}" alt="${p.name}">
                            </div>
                            <div class="chat-product-info">
                                <div class="chat-product-name">${p.name}</div>
                                ${bundleMeta?.role ? `<div class="chat-product-role">${bundleMeta.role}</div>` : ''}
                                <div class="chat-product-price">₹ ${p.price.toLocaleString()} <span class="chat-product-strike">₹ ${p.priceStrike.toLocaleString()}</span></div>
                                ${bundleMeta?.reason ? `<div class="chat-product-note">${bundleMeta.reason}</div>` : ''}
                                <div class="chat-product-actions">
                                    <button class="btn btn-xs btn-gold" onclick="selectProduct('${p.id}')">View Details</button>
                                    <button class="btn btn-xs btn-outline" onclick="quickCustomizeProduct('${p.id}')">Customize</button>
                                    <button class="btn btn-xs btn-dark" onclick="quickAddToCart('${p.id}')">+ Add to Bag</button>
                                </div>
                            </div>
                        </div>
                    `;
                }
            });
            if (cardsHTML) {
                widgetHTML += `
                    <div class="chat-widget-section">
                        <div class="chat-widget-title"><i class="fa-solid fa-sparkles text-gold"></i> Recommended Collections</div>
                        <div class="chat-products-carousel">${cardsHTML}</div>
                    </div>
                `;
            }
        }

        // 3. Visual Fabric Swatch Gallery Cards
        if (content.toLowerCase().includes('fabric') || actions.some(a => a.type === 'customize_fabric')) {
            const fabrics = [
                { name: "D 963/1 - Suit Soft stone", img: "/static/assets/fabric_soft_stone.jpg" },
                { name: "AC 103/1 - Suit Pearl", img: "/static/assets/fabric_pearl.jpg" },
                { name: "AW 268/1 - Jacket Cobalt blue", img: "/static/assets/fabric_cobalt.jpg" },
                { name: "V 712/3 - Bandhgala Burgundy", img: "/static/assets/fabric_burgundy.jpg" }
            ];
            widgetHTML += `
                <div class="chat-widget-section">
                    <div class="chat-widget-title"><i class="fa-solid fa-palette text-gold"></i> Premium Fabric Swatches:</div>
                    <div class="chat-fabrics-grid">
                        ${fabrics.map(f => `
                            <div class="chat-fabric-item" onclick="selectFabricFromChat('${f.name}')">
                                <div class="chat-fabric-img" style="background-image: url('${f.img}')"></div>
                                <span class="chat-fabric-name">${f.name}</span>
                                <button class="btn btn-xs btn-gold">Select</button>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        // 4. Doorstep Visit & Sizing Widget Card
        if (actions.some(a => ['request_measurements', 'schedule_technician'].includes(a.type)) || content.toLowerCase().includes('technician') || content.toLowerCase().includes('measurement')) {
            widgetHTML += `
                <div class="chat-widget-card">
                    <div class="chat-widget-title"><i class="fa-solid fa-tape text-gold"></i> Sizing & Tailor Visit Options:</div>
                    <p class="text-xs text-muted mt-1">Select your preferred fitting option in chat:</p>
                    <div class="chat-widget-actions mt-2">
                        <button class="btn btn-xs btn-gold" onclick="sendSuggestion('I choose Ready Size M with Slim Fit')">Slim Fit (Ready M)</button>
                        <button class="btn btn-xs btn-gold" onclick="sendSuggestion('I choose Ready Size L with Regular Fit')">Regular Fit (Ready L)</button>
                        <button class="btn btn-xs btn-outline" onclick="quickScheduleVisit('Mumbai')">🏠 Visit (Mumbai)</button>
                        <button class="btn btn-xs btn-outline" onclick="quickScheduleVisit('Bangalore')">🏠 Visit (Bangalore)</button>
                        <button class="btn btn-xs btn-outline" onclick="quickScheduleVisit('Gurgaon')">🏠 Visit (Gurgaon)</button>
                    </div>
                </div>
            `;
        }

        // 5. Cart / Checkout Widget Card
        if (actions.some(a => ['add_to_bag', 'open_cart'].includes(a.type)) || (state.cart.length > 0 && content.toLowerCase().includes('bag'))) {
            widgetHTML += `
                <div class="chat-widget-card gold-border">
                    <div class="chat-widget-title"><i class="fa-solid fa-bag-shopping text-gold"></i> Shopping Bag (${state.cart.length} items):</div>
                    <div class="mt-2">
                        <button class="btn btn-gold btn-sm w-full" onclick="toggleDrawer('cart-drawer', true)"><i class="fa-solid fa-cart-shopping"></i> Review Bag & Checkout</button>
                    </div>
                </div>
            `;
        }
    }

    msgDiv.innerHTML = `
        <div class="message-bubble">
            ${parsedContent}
            ${widgetHTML}
        </div>
    `;
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
                if (action.height) {
                    state.customization.height = action.height;
                    const el = document.getElementById('measure-height');
                    if (el) el.value = action.height;
                }
                if (action.body_type) {
                    state.customization.bodyType = action.body_type;
                    const el = document.getElementById('measure-body-type');
                    if (el) el.value = action.body_type;
                }
                
                // Ready sizes vs Custom measurements selection
                if (action.size_method) {
                    state.customization.sizeMethod = action.size_method;
                    
                    if (action.size_method === 'ready') {
                        if (action.ready_jacket_size) {
                            state.customization.readyJacketSize = action.ready_jacket_size;
                            const el = document.getElementById('ready-jacket-size');
                            if (el) el.value = action.ready_jacket_size;
                        }
                        if (action.ready_trouser_size) {
                            state.customization.readyTrouserSize = action.ready_trouser_size;
                            const el = document.getElementById('ready-trouser-size');
                            if (el) el.value = action.ready_trouser_size;
                        }
                    } else if (action.size_method === 'custom') {
                        if (action.fitting) {
                            state.customization.fitting = action.fitting;
                            const el = document.getElementById('custom-fitting');
                            if (el) el.value = action.fitting;
                        }
                        if (action.custom_measurements) {
                            const cm = action.custom_measurements;
                            if (cm.bust) state.customization.customMeasurements.bust = cm.bust;
                            if (cm.waist) state.customization.customMeasurements.waist = cm.waist;
                            if (cm.hips) state.customization.customMeasurements.hips = cm.hips;
                            if (cm.upper) state.customization.customMeasurements.upper = cm.upper;
                            if (cm.neck) state.customization.customMeasurements.neck = cm.neck;
                            if (cm.outer_arm) state.customization.customMeasurements.outerArm = cm.outer_arm;
                            if (cm.shoulder) state.customization.customMeasurements.shoulder = cm.shoulder;
                            if (cm.length) state.customization.customMeasurements.length = cm.length;
                            if (cm.width) state.customization.customMeasurements.width = cm.width;
                            if (cm.neck_point) state.customization.customMeasurements.neckPoint = cm.neck_point;
                            
                            if (cm.crotch) state.customization.customMeasurements.crotch = cm.crotch;
                            if (cm.cuff) state.customization.customMeasurements.cuff = cm.cuff;
                            if (cm.lower_hips) state.customization.customMeasurements.lowerHips = cm.lower_hips;
                            if (cm.thigh) state.customization.customMeasurements.thigh = cm.thigh;
                            if (cm.lower_length) state.customization.customMeasurements.lowerLength = cm.lower_length;
                        }
                    }
                }
                
                updateMonitor(`Result: Set height/sizes in session state`);
                break;
                
            case 'schedule_technician':
                if (action.city) {
                    state.appointment.city = action.city;
                    const el = document.getElementById('appt-city');
                    if (el) el.value = action.city;
                }
                if (action.date) {
                    state.appointment.date = action.date;
                    const el = document.getElementById('appt-date');
                    if (el) el.value = action.date;
                }
                updateMonitor(`Result: Configured technician scheduler: city=${action.city}, date=${action.date}`);
                break;
                
            case 'add_to_bag':
                // Wait short moment to let visual state reflect before adding
                await new Promise(resolve => setTimeout(resolve, 400));
                submitCustomization(true);
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
                updateMonitor('Result: Measurement workflow option presented in chat');
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
