const { useState, useEffect, useRef, useMemo } = React;
const { createRoot } = ReactDOM;

// --- HOOKS ---
const useGestureWebSocket = () => {
    const [data, setData] = useState(null);
    const ws = useRef(null);

    useEffect(() => {
        ws.current = new WebSocket(`ws://${window.location.host}/ws`);
        ws.current.onmessage = (event) => {
            const parsed = JSON.parse(event.data);
            setData(parsed);
        };
        return () => ws.current.close();
    }, []);

    const sendMode = (mode) => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ type: "SET_MODE", mode }));
        }
    };

    return { data, sendMode };
};

// --- COMPONENTS ---

const Background = () => {
    const canvasRef = useRef(null);
    const mouseRef = useRef({ x: null, y: null });

    useEffect(() => {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        let animationFrameId;

        // --- DEFINITIONS ---

        class Particle {
            constructor() {
                this.x = Math.random() * canvas.width;
                this.y = Math.random() * canvas.height;
                this.directionX = Math.random() * 0.4 - 0.2;
                this.directionY = Math.random() * 0.4 - 0.2;
                this.size = Math.random() * 2.5 + 1.5;
                this.color = 'rgba(80, 80, 80, 0.4)'; // Dark grey

                this.vx = 0;
                this.vy = 0;
                this.friction = 0.92;
            }

            draw() {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                ctx.fillStyle = this.color;
                ctx.fill();
            }

            update() {
                // 1. Constant Gentle Drift
                this.x += this.directionX;
                this.y += this.directionY;

                // 2. Mouse Interaction (Repel)
                if (mouseRef.current.x != null) {
                    let dx = mouseRef.current.x - this.x;
                    let dy = mouseRef.current.y - this.y;
                    let distance = Math.sqrt(dx * dx + dy * dy);
                    const forceRadius = 250;

                    if (distance < forceRadius) {
                        const force = (forceRadius - distance) / forceRadius;
                        const directionX = dx / distance;
                        const directionY = dy / distance;

                        const pushForce = -15;

                        this.vx += directionX * force * pushForce;
                        this.vy += directionY * force * pushForce;
                    }
                }

                // 3. Apply Physics
                this.x += this.vx;
                this.y += this.vy;

                this.vx *= this.friction;
                this.vy *= this.friction;

                // 4. Wrap around screen
                if (this.x > canvas.width + 10) this.x = -10;
                if (this.x < -10) this.x = canvas.width + 10;
                if (this.y > canvas.height + 10) this.y = -10;
                if (this.y < -10) this.y = canvas.height + 10;

                this.draw();
            }
        }

        let particlesArray = [];

        const init = () => {
            particlesArray = [];
            // Calculate effective area based on current canvas size
            const area = canvas.width * canvas.height;
            let numberOfParticles = area / 10000;
            for (let i = 0; i < numberOfParticles; i++) {
                particlesArray.push(new Particle());
            }
        };

        const connect = () => {
            for (let a = 0; a < particlesArray.length; a++) {
                for (let b = a; b < particlesArray.length; b++) {
                    let dx = particlesArray[a].x - particlesArray[b].x;
                    let dy = particlesArray[a].y - particlesArray[b].y;
                    let distance = dx * dx + dy * dy;

                    if (distance < 20000) {
                        let opacityValue = 1 - (distance / 20000);
                        ctx.strokeStyle = 'rgba(80, 80, 80,' + opacityValue * 0.2 + ')';
                        ctx.lineWidth = 1;
                        ctx.beginPath();
                        ctx.moveTo(particlesArray[a].x, particlesArray[a].y);
                        ctx.lineTo(particlesArray[b].x, particlesArray[b].y);
                        ctx.stroke();
                    }
                }
            }
        };

        const animate = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            for (let i = 0; i < particlesArray.length; i++) {
                particlesArray[i].update();
            }
            connect();
            animationFrameId = requestAnimationFrame(animate);
        };

        const handleResize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            init(); // Now safe to call as init is defined above
        };

        const handleMouseMove = (e) => {
            mouseRef.current.x = e.clientX;
            mouseRef.current.y = e.clientY;
        };

        const handleMouseLeave = () => {
            mouseRef.current.x = null;
            mouseRef.current.y = null;
        };

        // --- EXECUTION ---

        window.addEventListener('resize', handleResize);
        window.addEventListener('mousemove', handleMouseMove);
        window.addEventListener('mouseleave', handleMouseLeave);

        // Initial setup
        handleResize(); // Sets canvas size AND calls init()
        animate();      // Starts loop

        return () => {
            window.removeEventListener('resize', handleResize);
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseleave', handleMouseLeave);
            cancelAnimationFrame(animationFrameId);
        };
    }, []);

    return <canvas ref={canvasRef} className="fixed inset-0 z-0 bg-[#f8f9fa]" />;
};

const Hub = ({ setMode }) => {
    const modes = [
        { id: "AIR_DRAW", label: "Canvas", sub: "Digital Creation", icon: "brush" },
        { id: "SCROLLER", label: "Scroll", sub: "Kinetic Read", icon: "move" },
        { id: "3D_DRAW", label: "3D Drawing", sub: "3D Environment", icon: "box" }
    ];

    return (
        <div className="relative z-10 w-full h-full flex flex-col items-center justify-center p-12 custom-cursor-area">
            {/* Header */}
            <div className="absolute top-12 left-12">
                <h1 className="text-3xl font-serif text-gray-800 tracking-tight">
                    HandGesture<span className="text-purple-400">.</span>
                </h1>
                <p className="text-xs text-gray-400 tracking-[0.2em] mt-1 uppercase">
                    Fluid Interface v2.5
                </p>
            </div>

            {/* Menu Cards */}
            <div className="flex gap-8 items-center">
                {modes.map((m) => (
                    <button
                        key={m.id}
                        onClick={() => setMode(m.id)}
                        className="group relative w-64 h-80 bg-white/40 backdrop-blur-xl border border-white/60 rounded-[2rem] shadow-[0_8px_30px_rgb(0,0,0,0.04)] hover:shadow-[0_20px_50px_rgb(0,0,0,0.08)] transition-all duration-500 hover:-translate-y-2 flex flex-col items-center justify-center gap-6 overflow-hidden"
                    >
                        {/* Hover Gradient */}
                        <div className="absolute inset-0 bg-gradient-to-br from-white/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

                        <div className="relative z-10 w-16 h-16 rounded-2xl bg-white shadow-sm flex items-center justify-center text-gray-700 group-hover:scale-110 transition-transform duration-500">
                            {/* Simple icon placeholder - lucide icons handled via text for now or could integrate actual svg */}
                            <div className="w-8 h-8 rounded-full border-2 border-gray-200 group-hover:border-purple-300 transition-colors" />
                        </div>

                        <div className="relative z-10 text-center">
                            <h2 className="text-2xl font-serif text-gray-800 mb-1">{m.label}</h2>
                            <p className="text-xs text-gray-500 tracking-wider uppercase">{m.sub}</p>
                        </div>
                    </button>
                ))}
            </div>

            {/* Footer */}
            <div className="absolute bottom-12 text-gray-400 text-xs tracking-widest">
                INTERACTIVE GESTURE SYSTEM
            </div>
        </div>
    );
};

const AirCanvas = ({ gestureData }) => {
    const canvasRef = useRef(null);
    const [color, setColor] = useState("#1a1a1a");
    const [brushSize, setBrushSize] = useState(4);
    const [tool, setTool] = useState("pen"); // pen, marker, eraser, brush

    // Previous cursor position for smoothing lines
    const prevPos = useRef({ x: null, y: null });

    const tools = [
        { id: "pen", icon: "✏️", label: "Pencil", size: 2, opacity: 1 },
        { id: "brush", icon: "🖌️", label: "Brush", size: 8, opacity: 0.8 },
        { id: "marker", icon: "🖍️", label: "Marker", size: 15, opacity: 0.4 },
        { id: "eraser", icon: "🧼", label: "Eraser", size: 30, opacity: 1 }
    ];

    const palette = [
        "#1a1a1a", "#78716c", "#ef4444", "#f97316", "#f59e0b", "#84cc16",
        "#10b981", "#06b6d4", "#3b82f6", "#6366f1", "#8b5cf6", "#d946ef",
        "#f43f5e", "#881337", "#ffffff"
    ];

    useEffect(() => {
        const cvs = canvasRef.current;
        cvs.width = window.innerWidth;
        cvs.height = window.innerHeight;
        const ctx = cvs.getContext("2d");
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
    }, []);

    useEffect(() => {
        if (!gestureData || !gestureData.cursor) return;
        const ctx = canvasRef.current.getContext("2d");
        const { x, y } = gestureData.cursor;

        // Convert normalized to pixels
        const px = x * window.innerWidth;
        const py = y * window.innerHeight;

        // CHECK UI INTERACTION: Don't draw over buttons/inputs
        const element = document.elementFromPoint(px, py);
        const isInteractive = element && (
            element.tagName === 'BUTTON' ||
            element.tagName === 'INPUT' ||
            element.closest('button') ||
            element.closest('input') ||
            element.closest('.toolbar-container') // Future proof if I add class
        );

        if (isInteractive) {
            prevPos.current = { x: null, y: null };
            return;
        }

        if (gestureData.is_pinched) {
            ctx.beginPath();

            // Start from previous position or current if null
            if (prevPos.current.x === null) {
                ctx.moveTo(px, py);
            } else {
                ctx.moveTo(prevPos.current.x, prevPos.current.y);
            }

            ctx.lineTo(px, py);

            // Tool Settings
            let actualColor = tool === 'eraser' ? '#f8f9fa' : color;
            let actualSize = tool === 'eraser' ? 50 : brushSize;
            let opacity = 1;

            if (tool === 'marker') {
                opacity = 0.1; // Buildup effect
                actualSize = brushSize * 3;
            } else if (tool === 'brush') {
                actualSize = brushSize * 1.5;
            }

            ctx.globalAlpha = opacity;
            ctx.strokeStyle = actualColor;
            ctx.lineWidth = actualSize;
            ctx.stroke();
            ctx.globalAlpha = 1.0; // Reset

            prevPos.current = { x: px, y: py };
        } else {
            // Lift pen
            prevPos.current = { x: null, y: null };
        }
    }, [gestureData, color, brushSize, tool]);

    // Update brush size defaults when tool changes
    useEffect(() => {
        const t = tools.find(t => t.id === tool);
        if (t && t.id !== 'eraser') setBrushSize(t.size);
    }, [tool]);

    return (
        <div className="relative w-full h-full pointer-events-none"> {/* Pass-through for canvas */}
            <canvas ref={canvasRef} className="absolute inset-0 z-10" />

            {/* Floating Toolbar (Pointer events enabled for UI) */}
            <div className="absolute top-8 left-8 flex flex-col gap-4 pointer-events-auto">

                {/* Tools Panel */}
                <div className="bg-white/80 backdrop-blur-xl p-4 rounded-3xl shadow-xl border border-white/50 flex flex-col gap-4">
                    <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest text-center">Tools</h3>
                    <div className="grid grid-cols-2 gap-2">
                        {tools.map(t => (
                            <button
                                key={t.id}
                                onClick={() => setTool(t.id)}
                                className={`p-3 rounded-xl flex flex-col items-center justify-center transition-all ${tool === t.id ? 'bg-purple-100 ring-2 ring-purple-400' : 'hover:bg-gray-100'}`}
                            >
                                <span className="text-2xl">{t.icon}</span>
                                <span className="text-[10px] text-gray-500 font-medium">{t.label}</span>
                            </button>
                        ))}
                    </div>

                    {/* Size Slider */}
                    {tool !== 'eraser' && (
                        <div className="px-2 pt-2">
                            <label className="text-[10px] text-gray-400 font-bold uppercase mb-1 block">Size: {brushSize}px</label>
                            <input
                                type="range"
                                min="1"
                                max="50"
                                value={brushSize}
                                onChange={(e) => setBrushSize(parseInt(e.target.value))}
                                className="w-full accent-purple-500 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                            />
                        </div>
                    )}
                </div>

                {/* Color Palette */}
                {tool !== 'eraser' && (
                    <div className="bg-white/80 backdrop-blur-xl p-4 rounded-3xl shadow-xl border border-white/50">
                        <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest text-center mb-3">Palette</h3>
                        <div className="grid grid-cols-3 gap-2">
                            {palette.map(hex => (
                                <button
                                    key={hex}
                                    onClick={() => setColor(hex)}
                                    className={`w-8 h-8 rounded-full border border-gray-100 shadow-sm transition-transform ${color === hex ? 'scale-125 ring-2 ring-gray-300 z-10' : 'hover:scale-110'}`}
                                    style={{ backgroundColor: hex }}
                                />
                            ))}
                        </div>
                    </div>
                )}
            </div>

            <div className="absolute top-8 left-1/2 transform -translate-x-1/2 opacity-30 pointer-events-none">
                <h2 className="font-serif text-2xl text-gray-800">Canvas Mode</h2>
            </div>
        </div>
    );
};

const ScrollerOverlay = ({ gestureData }) => {
    const isScrolling = gestureData?.scroll_delta !== 0;

    return (
        <div className="flex flex-col items-center justify-center h-full relative z-10">
            {isScrolling && (
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <h1 className="font-serif text-[12rem] text-gray-900/5 mix-blend-overlay">
                        {gestureData?.scroll_delta < 0 ? "↓" : "↑"}
                    </h1>
                </div>
            )}

            <div className={`transition-all duration-500 ${isScrolling ? 'scale-110' : 'scale-100'}`}>
                <div className="w-1 h-32 bg-gray-200 rounded-full overflow-hidden relative">
                    <div
                        className={`absolute w-full bg-gray-800 transition-all duration-100 ${isScrolling ? 'h-full opacity-100' : 'h-8 opacity-50 top-0'}`}
                        style={{
                            top: gestureData?.scroll_delta < 0 ? 'auto' : 0,
                            bottom: gestureData?.scroll_delta < 0 ? 0 : 'auto',
                            height: isScrolling ? '100%' : '20%'
                        }}
                    />
                </div>
            </div>

            <p className="mt-8 text-sm text-gray-400 font-serif tracking-widest uppercase opacity-60">
                {isScrolling ? "Scrolling" : "Pinch to Scroll"}
            </p>
        </div>
    );
};

const ThreeCanvas = ({ gestureData }) => {
    const mountRef = useRef(null);

    useEffect(() => {
        const scene = new THREE.Scene();
        // Light background for the theme
        scene.background = new THREE.Color(0xf8f9fa);

        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ antialias: true });

        renderer.setSize(window.innerWidth, window.innerHeight);
        mountRef.current.appendChild(renderer.domElement);

        // Abstract Shape
        const geometry = new THREE.TorusKnotGeometry(10, 3, 100, 16);
        const material = new THREE.MeshPhysicalMaterial({
            color: 0xe9d5ff, // Soft Purple
            roughness: 0.1,
            metalness: 0.1,
            transmission: 0.9, // Glass-like
            thickness: 1,
            clearcoat: 1,
        });
        const mesh = new THREE.Mesh(geometry, material);
        scene.add(mesh);

        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
        scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xffffff, 1);
        dirLight.position.set(5, 10, 7);
        scene.add(dirLight);

        camera.position.z = 30;

        const animate = () => {
            requestAnimationFrame(animate);
            mesh.rotation.x += 0.005;
            mesh.rotation.y += 0.005;
            renderer.render(scene, camera);
        };
        animate();

        return () => {
            mountRef.current.removeChild(renderer.domElement);
        }
    }, []);

    return <div ref={mountRef} className="absolute inset-0 z-0" />;
};

const CustomCursor = ({ x, y, isPinched }) => (
    <div
        className="fixed pointer-events-none z-[100] mix-blend-difference flex items-center justify-center transition-transform duration-75"
        style={{
            left: x * window.innerWidth,
            top: y * window.innerHeight,
            transform: `translate(-50%, -50%) scale(${isPinched ? 0.8 : 1})`
        }}
    >
        <div className={`w-8 h-8 border border-white rounded-full transition-all duration-300 ${isPinched ? 'bg-white scale-50' : ''}`} />
        <div className="absolute w-1 h-1 bg-white rounded-full" />
    </div>
);

const App = () => {
    const [mode, setMode] = useState("HUB");
    const { data, sendMode } = useGestureWebSocket();
    const [cursorPos, setCursorPos] = useState({ x: 0.5, y: 0.5 });

    useEffect(() => {
        sendMode(mode);
    }, [mode]);

    useEffect(() => {
        if (data?.cursor) {
            setCursorPos(data.cursor);
        }
    }, [data]);

    return (
        <div className="h-full w-full overflow-hidden text-gray-800">
            <Background />

            {/* Application Layer */}
            <div className="relative z-10 h-full">
                {/* Back Navigation */}
                {mode !== "HUB" && (
                    <button
                        onClick={() => setMode("HUB")}
                        className="fixed top-8 right-8 z-50 text-gray-400 hover:text-gray-800 transition-colors"
                    >
                        <span className="font-serif italic text-lg hover:underline decoration-1 underline-offset-4">Close</span>
                    </button>
                )}

                {/* Main Content */}
                {mode === "HUB" && <Hub setMode={setMode} />}
                {mode === "AIR_DRAW" && <AirCanvas gestureData={data} />}
                {mode === "SCROLLER" && <ScrollerOverlay gestureData={data} />}
                {mode === "3D_DRAW" && <ThreeCanvas gestureData={data} />}
            </div>

            {/* Gesture Cursor */}
            {data && <CustomCursor x={cursorPos.x} y={cursorPos.y} isPinched={data.is_pinched} />}
        </div>
    );
};

const root = createRoot(document.getElementById("root"));
root.render(<App />);
