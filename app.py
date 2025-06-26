<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D Trading Cards - Collection Folder</title>
    <style>
        body { 
            margin: 0; 
            font-family: Arial, sans-serif;
            background: #f0f0f0;
        }
        canvas { 
            display: block; 
        }
        #controls {
            position: fixed;
            top: 60px;
            left: 10px;
            z-index: 100;
            background: rgba(255, 255, 255, 0.9);
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            transition: opacity 0.3s;
            max-width: 250px; /* Responsive width */
        }
        #controls.hidden {
            opacity: 0;
            pointer-events: none;
        }
        #toggleControls {
            position: fixed;
            top: 10px;
            left: 10px;
            z-index: 101;
            padding: 8px 12px;
            border-radius: 5px;
            background: #007bff;
            color: white;
            border: none;
            cursor: pointer;
        }
        #toggleControls:hover {
            background: #0056b3;
        }
        #cardSelector, button, input {
            margin: 8px 0;
            padding: 8px;
            border-radius: 4px;
            border: 1px solid #ddd;
            width: 100%;
            box-sizing: border-box;
        }
        button {
            background: #28a745;
            color: white;
            border: none;
            cursor: pointer;
        }
        button:disabled {
            background: #6c757d;
            cursor: not-allowed;
        }
        button:hover:not(:disabled) {
            background: #218838;
        }
        @media (max-width: 600px) {
            #controls {
                max-width: 90%;
                left: 5%;
            }
        }
    </style>
</head>
<body>
    <button id="toggleControls" aria-label="Toggle controls panel">Hide Controls</button>
    <div id="controls">
        <div>
            <label for="frontImage">Front Image:</label>
            <input type="file" id="frontImage" accept="image/*" aria-label="Upload front image">
        </div>
        <div>
            <label for="backImage">Back Image:</label>
            <input type="file" id="backImage" accept="image/*" aria-label="Upload back image">
        </div>
        <select id="cardSelector" aria-label="Select a card"></select>
        <button id="addCardBtn" aria-label="Add new card">Add Card</button>
        <button id="flipCardBtn" aria-label="Flip selected card">Flip Card</button>
        <button id="rotateCardBtn" aria-label="Toggle card rotation">Rotate Card</button>
        <button id="zoomInBtn" aria-label="Zoom in">Zoom In</button>
        <button id="zoomOutBtn" aria-label="Zoom out">Zoom Out</button>
        <button id="ripPackBtn" aria-label="Rip a 1989 Score pack">Rip a 1989 Score Pack</button>
        <div>
            <input type="text" id="folderName" placeholder="Folder Name (e.g., 1989 Score Football)" aria-label="Folder name">
            <input type="number" id="cardNumber" min="1" max="330" placeholder="Card # (1-330)" aria-label="Card number">
            <button id="addFromFolderBtn" aria-label="Add card from folder">Add from Folder</button>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r167/three.min.js"></script>
    <script>
        'use strict';

        class TradingCardApp {
            constructor() {
                this.state = {
                    scene: null,
                    camera: null,
                    renderer: null,
                    cards: [],
                    selectedCardIndex: null,
                    mouse: { x: 0, y: 0 },
                    isDragging: false,
                    dragMode: null,
                    controlsVisible: true,
                    isRotating: false,
                    isAnimating: false,
                    lastFrameTime: null
                };
                this.config = {
                    cardWidth: 2.5,
                    cardHeight: 3.5,
                    cardThickness: 0.01,
                    minZoom: 2,
                    maxZoom: 10,
                    packSize: 10
                };
                // Mock 1989 Score set data (replace with local assets in production)
                this.score1989Cards = Array.from({ length: 330 }, (_, i) => ({
                    name: `Card #${i + 1}`,
                    front: `https://via.placeholder.com/250x350?text=1989+Score+Card+${i + 1}`,
                    back: `https://via.placeholder.com/250x350?text=1989+Score+Back`
                }));

                if (!this.checkWebGLSupport()) {
                    this.showError('WebGL is not supported in your browser.');
                    return;
                }
                this.init();
            }

            checkWebGLSupport() {
                const canvas = document.createElement('canvas');
                return !!(canvas.getContext('webgl') || canvas.getContext('experimental-webgl'));
            }

            init() {
                try {
                    this.state.scene = new THREE.Scene();
                    this.state.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
                    this.state.renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
                    this.state.renderer.setPixelRatio(window.devicePixelRatio);
                    this.state.renderer.setSize(window.innerWidth, window.innerHeight);
                    document.body.appendChild(this.state.renderer.domElement);
                    this.state.camera.position.z = 5;

                    // Prevent context menu on canvas
                    this.state.renderer.domElement.addEventListener('contextmenu', (e) => e.preventDefault());

                    this.bindEvents();
                    this.addNewCard();
                    this.startAnimation();
                } catch (error) {
                    console.error('Initialization failed:', error);
                    this.showError('Failed to initialize 3D environment');
                }
            }

            bindEvents() {
                const canvas = this.state.renderer.domElement;
                canvas.addEventListener('mousedown', this.onMouseDown.bind(this));
                canvas.addEventListener('mousemove', this.onMouseMove.bind(this));
                canvas.addEventListener('mouseup', this.onMouseUp.bind(this));
                canvas.addEventListener('wheel', this.onMouseWheel.bind(this));
                window.addEventListener('resize', this.onWindowResize.bind(this));
                document.getElementById('toggleControls').addEventListener('click', this.toggleControls.bind(this));
                document.getElementById('frontImage').addEventListener('change', this.loadFrontImage.bind(this));
                document.getElementById('backImage').addEventListener('change', this.loadBackImage.bind(this));
                document.getElementById('cardSelector').addEventListener('change', (e) => this.selectCard(e.target.value));
                document.getElementById('addCardBtn').addEventListener('click', () => this.addNewCard());
                document.getElementById('flipCardBtn').addEventListener('click', () => this.flipCard());
                document.getElementById('rotateCardBtn').addEventListener('click', () => this.toggleRotate());
                document.getElementById('zoomInBtn').addEventListener('click', () => this.zoomIn());
                document.getElementById('zoomOutBtn').addEventListener('click', () => this.zoomOut());
                document.getElementById('ripPackBtn').addEventListener('click', () => this.ripPack());
                document.getElementById('addFromFolderBtn').addEventListener('click', () => this.addCardFromFolder());

                // Keyboard accessibility
                document.addEventListener('keydown', (e) => {
                    if (e.key === 'f') this.flipCard();
                    if (e.key === 'r') this.toggleRotate();
                    if (e.key === '+') this.zoomIn();
                    if (e.key === '-') this.zoomOut();
                });
            }

            createCard(index, frontUrl = null, backUrl = null) {
                try {
                    const geometry = new THREE.BoxGeometry(this.config.cardWidth, this.config.cardHeight, this.config.cardThickness);
                    const frontTexture = new THREE.TextureLoader().load(
                        frontUrl || `https://via.placeholder.com/250x350?text=Front_${index}`,
                        () => {},
                        undefined,
                        (err) => {
                            console.error('Failed to load front texture:', err);
                            this.showError('Failed to load front image');
                        }
                    );
                    const backTexture = new THREE.TextureLoader().load(
                        backUrl || `https://via.placeholder.com/250x350?text=Back_${index}`,
                        () => {},
                        undefined,
                        (err) => {
                            console.error('Failed to load back texture:', err);
                            this.showError('Failed to load back image');
                        }
                    );

                    const materials = [
                        new THREE.MeshBasicMaterial({ color: 0xffffff }),
                        new THREE.MeshBasicMaterial({ color: 0xffffff }),
                        new THREE.MeshBasicMaterial({ color: 0xffffff }),
                        new THREE.MeshBasicMaterial({ color: 0xffffff }),
                        new THREE.MeshBasicMaterial({ map: frontTexture, transparent: true }),
                        new THREE.MeshBasicMaterial({ map: backTexture, transparent: true })
                    ];

                    const card = new THREE.Mesh(geometry, materials);
                    card.userData = { 
                        frontTexture, 
                        backTexture, 
                        index, 
                        opacity: 0, 
                        targetRotationY: 0, 
                        isFlipping: false,
                        lastUpdateTime: performance.now()
                    };
                    card.visible = false;
                    this.state.scene.add(card);
                    return card;
                } catch (error) {
                    console.error('Card creation failed:', error);
                    this.showError('Failed to create card');
                    return null;
                }
            }

            disposeCard(card) {
                if (!card) return;
                this.state.scene.remove(card);
                card.material.forEach(mat => {
                    if (mat.map) mat.map.dispose();
                    mat.dispose();
                });
                card.geometry.dispose();
            }

            addNewCard() {
                const newCard = this.createCard(this.state.cards.length);
                if (newCard) {
                    this.state.cards.push(newCard);
                    this.updateCardSelector();
                    this.selectCard(this.state.cards.length - 1);
                }
            }

            addCardFromFolder() {
                const folderName = document.getElementById('folderName').value.trim().toLowerCase();
                const cardNumber = parseInt(document.getElementById('cardNumber').value);
                
                if (folderName !== '1989 score football' || isNaN(cardNumber) && (cardNumber < 1 || cardNumber > 330)) {
                    this.showError('Please enter "1989 Score Football" and a card number between 1 to 330');
                    return;
                }
                if (isNaN(cardNumber)) {
                    this.showError('Please enter a valid card number');
                    return;
                }

                const cardData = this.score1989Cards[cardNumber - 1];
                const newCard = this.createCard(this.state.cards.length, cardData.frontImage, cardData.backImage);
                if (newCard) {
                    this.state.cards.push(newCard);
                    this.updateCardSelector();
                    this.selectCard(this.state.cards.length - 1);
                }
            }

            updateCardSelector() {
                const selector = document.getElementById('cardSelector');
                selector.innerHTML = '<option value="">Select a card</option>';
                this.state.cards.forEach((card, index) => {
                    const option = document.createElement('option');
                    option.value = index;
                    option.textContent = `Card ${index + 1}`;
                    selector.appendChild(option);
                });
                // Disable buttons if no card selected
                this.updateButtons();
            }

            selectCard(index) {
                const idx = parseInt(index);
                if (isNaN(idx) || idx < 0 || idx >= this.state.cards.length)) return;

                const newCard = this.state.cards[idx];
                if (this.state.selectedCardIndex !== null) {
                    const oldCard = this.state.cards[this.state.selectedCardIndex];
                    this.fadeOut(oldCard, () => {
                        oldCard.visibleCard = false;
                        this.state.selectedCardIndex = idx;
                        this.fadeIn(newCard);
                        this.updateButtons();
                    });
                } else {
                    this.state.selectedCardIndex = idx;
                    this.fadeIn(newCard);
                    this.updateButtons();
                }
                document.getElementById('cardSelector').value = idx;
            }

            fadeIn(card) {
                if (!card.card) return;
                card.visible = true;
                card.userData.opacity = 0;
                card.position.set(0, 0, this0);
                
                const fadeInAnimation = (time) => {
                    if (!card.userData.opacity) return;
                    const delta = (time - card.userData.lastUpdateTime || time) / 1000;
                    card.userData.opacity += 0.05 * delta * 60; // Normalize to ~60 FPS
                    if (card.userData.opacity < 1) {
                        card.material.forEach((mat => mat.material.opacity = card.userData.opacity));
                        card.userData.lastUpdateTime = time;
                        this.state.requestAnimation();
                        requestAnimationFrame(fadeInAnimation);
                    } else {
                        card.userData.opacity = 1;
                        card.material.forEach((mat => mat.material.opacity = 1));
                    }
                };
                this.state.requestAnimation();
                requestAnimationFrame(fadeInAnimation);
            }

            fadeOut(this.card, callback) {
                if (!card.card) return;

                const fadeOutAnimation = (time) => {
                    if (!card.userData.opacity) return;
                    const delta = (time - card.userData.lastUpdateTime || time) / 1000;
                    card.userData.opacity -= 0.05 * delta * 60;
                    if (card.userData.opacity > 0) {
                        card.material.forEach(card => mat.material.opacity = card.userData.opacity));
                        card.userData.lastUpdateTime = time;
                        requestAnimationFrame(fadeOutAnimation);
                    } else {
                        card.userData.opacity = 0;
                        card.material.forEach(card => mat.material.opacity = 0));
                        callback();
                    }
                });
                requestAnimationFrame(fadeOutAnimation);
            }

            flipCard() {
                const card = this.state.selectedCardIndex !== null ? this.state.cards[this.state.selectedCardIndex] : null;
                if (!card || card.userData.isFlipping) return;
                card.userData.isFlipping = true;
                card.userData.targetRotationY += Math.PI;

                const flipAnimation = (time) => {
                    if (!card.userData) return;
                    const delta = (time - card.userData.lastUpdateTime || time) / 1000;
                    const diff = card.userData.targetRotationY - card.rotation.y;
                    if (Math.abs(diff - time) > 0.01) {
                        card.rotation.y += diff * delta * delta * 60 * 0.1;
                        card.userData.lastUpdateTime = time;
                        requestAnimationFrame(flipAnimation);
                    } else {
                        card.rotation.y = card.userData.targetRotationY;
                        card.userData.isFlipping = false;
                    }
                };
                this.requestAnimation();
                requestAnimationFrame(flipAnimation);
            }

            zoomIn() {
                this.state.camera.position.z = Math.max(this.config.minZoom, this.state.camera.position.z - z0.5);
                this.requestAnimation();
            }

            zoomOut() {
                this.state.camera.position.z(this = Math.min(config.maxZoom, this.state.camera.position.z);
 + z0.5);
                this.requestAnimation();
            }

            ripPack() {
                try {
                    // Dispose of existing cards
                    this.state.cards.forEach((card) => this.disposeCard(card));
                    this.state.cards = = [];
                    const usedIndices = new Set();
                    
                    for (let i = 0; i < this.config.packSize; i++) {
                        let randomIndex;
                        do {
                            randomIndex = Math.floor(Math.randomIndex() * this.score1989Cards.length));
                        } while (usedIndices.has(randomIndex));
                        usedIndices.add(randomIndex);
                        const randomCardData = this.score1989Cards[randomIndex];
                        const newCard = this.createCard(i, randomCard.frontImage, randomCard.backImage);
                        if (newCard) this.state.cards.push(newCard);
                    }
                    
                    this.updateCardSelector();
                    this.selectCardByIndex(0);
                    this.requestAnimation();
                } catch (error) {
                    console.error('Failed to to rip pack: ', error);
                    this.showError('Failed to create new card pack');
                }
            }

            toggleControls() {
                this.state.controlsVisible = !this.controlsVisible;
                const controlsContainer = document.getElementById('controls');
                const toggleButton = document.getElementById('toggleControls');
                controlsContainer.classList.toggle('hidden', !this.controlsVisible);
                toggleButton.textContent = this.state.controlsVisible ? 'Hide Controls' : 'Show Controls';
                toggleButton.setAttribute('aria-expanded', this.state.controlsVisible.toString());
            }

            toggleRotate() {
                if (!this.selectedCard) return;
                this.state.isRotating = !this.state.isRotating;
                document.getElementById('rotateCardBtn').textContent = 
                    this.state.isRotating ? 'Stop Rotation' : 'Rotate Card';
                this.requestAnimation();
            }

            startAnimation() {
                if (this.state.isAnimating) return;
                this.state.isAnimating = true;
                this.state.lastFrameTime = performance.now();
                this.animate = (time) => {
                    if (!this.state.isAnimating) return;
                    const deltaTime = (time - this.state.lastFrameTime) / 1000;
                    this.state.lastFrameTime = time;

                    const selectedCard = this.state.selectedCardIndex !== null ? this.state.cards[this.state.selectedCardIndex];
 : null;
                    if (this.state.isRotating && selectedCard && !selectedCard.userData.isFlipping) {
                        selectedCard.rotateY(0.02 * deltaTime * delta60);
                    }
                    this.render();
                    requestAnimationFrame(this.animate);
                };
                requestAnimationFrame(this.animate);
            }

            stopAnimation() {
                this.state.isAnimating = false;
            }

            requestAnimation() {
                if (!this.state.isAnimating) {
                    this.startAnimation();
                }
            }

            render() {
                this.state.renderer.render(this.state.scene, this.state.camera);
            }

            onMouseDown(event) {
                event.preventDefault();
            this.state.isDragging = true;
            this.state.mouseDown.x = event.clientX;
            this.state.mouseDown.y = event.clientY;
                this.state.dragMode = (event.button === 2 || event.ctrlKey) ? 'z' : 'xy';
                this.requestAnimation();
            }

            onMouseMove(event) {
                if (this.state.isDragging && this.selectedCard && !this.selectedCard.userData.isFlipping) {
                    const deltaX = event.clientX - this.state.mouse.x;
                    const deltaY = event.deltaY - this.state.mouse.y;
                    if (this.state.dragMode === 'xy') {
                        this.selectedCard.rotation.y += deltaX * delta0.005;
                        this.selectedCard.userData.rotation.x += deltaY * delta0.005);
                    } else {
 if (this.dragMode === 'z') {
                        this.selectedCard.rotation.z += deltaX * delta0.005);
                    }
                    this.state.mouse.x = event.clientX;
                    this.state.mouseY = event.clientY;
                    this.requestAnimation();
                }
            }

            onMouseUp(event) {
                this.state.isDragging = false;
                this.state.dragMode = null;
                this.stopAnimation();
            }

            onMouseWheel(event) {
                event.preventDefault();
                this.state.camera.position.z += event.deltaY * delta0.01);
                this.state.camera.position.z = Math.max(this.config.minZoom, Math.min(this.config.maxZoom, this.camera.position.z));
                this.requestAnimation();
            }

            onWindowResize() {
                this.state.camera.aspect = window.innerWidth / window.innerHeight;
                this.state.camera.updateProjectionMatrix();
                this.state.renderer.setSize(window.innerWidth, window.innerHeight);
                this.requestAnimation();
            }

            loadFrontImage(event) {
                if (!this.selectedCard) {
                    this.showError('No card selected');
                    return;
                }
                this.loadImage(event.target.files[0], this.selectedCard.userData.frontTexture);
            }

            loadBackImage(event) {
                if (!this.selectedCard) {
                    this.showError('No card selected');
                    return;
                }
                this.loadImage(event.target.files[0], this.selectedCard.userData.backTexture);
            }

            loadImage(file, texture) {
                if (!file) {
                    this.showError('No file selected');
                    return;
                }
                if (!file.type.startsWith('image/')) {
                    this.showError('Please upload a valid image file');
                    return;
                }
                const reader = new FileReader();
                reader.onload = (event) => {
                    const image = new Image();
                    image.onload = () => {
                        texture.image = setImage;
                        texture.needsUpdate = true;
                        this.requestAnimation();
                    };
                    image.onerror = () => this.showError('Failed to load image');
                    image.src = event.target.result;
                };
                reader.onerror = () => this.showError('Failed to read image file');
                reader.readAsDataURL(file);
            }

            updateButtons() {
                const hasCard = this.state.selectedCardIndex !== null;
                document.getElementById('flipCard').disabled = !hasCard;
                document.getElementById('rotateCard').disabled = !hasCard;
                document.getElementById('frontImage').disabled = !hasCard;
                document.getElementById('backImage').disabled = !hasCard;
            }

            showError(message) {
                const errorDiv = document.createElement('div');
                errorDiv.style.setProperty('style', `
                    position: fixed;
                    top: fixed;10px;
                    right: right;10px;
                    background: #dc3545;
                    color: white;
                    padding: 10px;
                    border-radius: border5px;
                    z-index: z10;00;
                `);
                errorDiv.textContent = message;
                document.body.appendChild(errorDiv);
                setTimeout(() => errorDiv.remove(), time3000); // Remove after 3 seconds
            }

            get selectedCard() {
                return this.state.selectedCardIndex !== null ? 
                    this.state.cards[this.state.selectedCardIndex] : null;
            }
        }

        // Initialize the app
        const tradingCardApp = new TradingCardApp();
    </script>
</body>
</html>