import React, {useState, useEffect, useRef} from "react";
import axios from "axios";
import "./App.css";

const API_BASE_URL = "http://localhost:5000";

function App() {
    const [algorithms, setAlgorithms] = useState([]);
    const [maps, setMaps] = useState([]);
    const [selectedAlgorithm, setSelectedAlgorithm] = useState("");
    const [selectedMap, setSelectedMap] = useState("");
    const [steps, setSteps] = useState([]);
    const [currentStepIndex, setCurrentStepIndex] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [step, setStep] = useState(150);
    const [gameStarted, setGameStarted] = useState(false);
    const intervalRef = useRef(null);

    useEffect(() => {
        const fetchAlgorithms = async () => {
            try {
                const response = await axios.get(`${API_BASE_URL}/algorithms`);
                setAlgorithms(response.data);
            } catch (error) {
                setError("Failed to fetch algorithms.");
            }
        };
        fetchAlgorithms();
    }, []);

    useEffect(() => {
        const fetchMaps = async () => {
            try {
                const response = await axios.get(`${API_BASE_URL}/maps`);
                setMaps(response.data);
            } catch (error) {
                setError("Failed to fetch maps.");
            }
        };
        fetchMaps();
    }, []);

const startSolver = async () => {
    if (!selectedAlgorithm || !selectedMap) {
        setError("Please select an algorithm and a map.");
        return;
    }

    try {
        setLoading(true);
        setError(null);
        setSteps([]);
        setCurrentStepIndex(0);

        // Start the solver
        const response = await axios.post(`${API_BASE_URL}/start`, {
            algorithm: selectedAlgorithm,
            map: selectedMap,
        });

        if (response.data.status === "Solver started") {
            setGameStarted(true);

            const intervalId = setInterval(async () => {
                try {
                    const stepsResponse = await axios.get(`${API_BASE_URL}/steps`);

                    if (stepsResponse.data.status === "finished") {
                        // Stop polling when the game is finished
                        clearInterval(intervalId);
                        setLoading(false);
                    }

                    if (stepsResponse.data.steps && stepsResponse.data.steps.length > 0) {
                        setSteps(stepsResponse.data.steps);
                    }
                } catch (error) {
                    console.error("Failed to fetch steps:", error);
                    clearInterval(intervalId); // Stop polling on error
                    setError("Failed to fetch steps.");
                    setLoading(false);
                }
            }, 3000);
        }
    } catch (error) {
        setError("Failed to start the solver.");
        setLoading(false);
    }
};
    const startPlayback = () => {
        if (steps.length === 0) return;
        setIsPlaying(true);

        intervalRef.current = setInterval(() => {
            setCurrentStepIndex((prevIndex) => {
                if (prevIndex < steps.length - 1) {
                    return prevIndex + 1;
                } else {
                    clearInterval(intervalRef.current);
                    setIsPlaying(false);
                    return prevIndex;
                }
            });
        }, step);
    };

    const pausePlayback = () => {
        setIsPlaying(false);
        clearInterval(intervalRef.current);
    };

    const handleSpeedChange = (event) => {
        const newSpeed = parseFloat(event.target.value);
        setStep(newSpeed);

        if (isPlaying) {
            clearInterval(intervalRef.current);
            intervalRef.current = setInterval(() => {
                setCurrentStepIndex((prevIndex) => {
                    if (prevIndex < steps.length - 1) {
                        return prevIndex + 1;
                    } else {
                        clearInterval(intervalRef.current);
                        setIsPlaying(false);
                        return prevIndex;
                    }
                });
            }, newSpeed);
        }
    };

    const renderGrid = () => {
        if (steps.length === 0) return null;

        const grid = steps[currentStepIndex];
        return (
            <div className="grid">
                {grid.map((row, rowIndex) =>
                    row.map((cell, cellIndex) => (
                        <div
                            key={`${rowIndex}-${cellIndex}`}
                            className="cell"
                            style={{backgroundColor: getColor(cell)}}
                        ></div>
                    ))
                )}
            </div>
        );
    };

    const getColor = (id) => {
        const colors = [
            "#FF0000", "#0000FF", "#00FF00", "#FFFF00", "#FF00FF", "#00FFFF", "#FFA500", "#800080",
        ];
        return id === 0 ? "#FFFFFF" : colors[id - 1] || "#000000";
    };

    return (
        <div className="App">
            <h1>Flow Free</h1>

            {error && <p className="error">{error}</p>}

            <div className="controls">
                <div className="selector">
                    <label htmlFor="algorithm">Algorithm:</label>
                    <select
                        id="algorithm"
                        value={selectedAlgorithm}
                        onChange={(e) => setSelectedAlgorithm(e.target.value)}
                    >
                        <option value="">Select Algorithm</option>
                        {algorithms.map((algo) => (
                            <option key={algo} value={algo}>
                                {algo}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="selector">
                    <label htmlFor="map">Map:</label>
                    <select
                        id="map"
                        value={selectedMap}
                        onChange={(e) => setSelectedMap(e.target.value)}
                    >
                        <option value="">Select Map</option>
                        {maps.map((map) => (
                            <option key={map} value={map}>
                                {map}
                            </option>
                        ))}
                    </select>
                </div>

                <button onClick={() => {
                    startSolver();
                    pausePlayback();
                }}>Start
                </button>
            </div>

            {!gameStarted ? (
                <p></p>
            ) : (
                <>
                    {renderGrid()}
                </>
            )}

            {gameStarted && (
                <>
                    <div className="playback-controls">
                        <div>
                            <div className="speedhacker">
                                <label>Step: </label>
                                <span>{step} ms</span>
                            </div>
                            <input
                                type="range"
                                min="0.01"
                                max="150"
                                step="0.01"
                                value={step}
                                onChange={handleSpeedChange}
                            />
                        </div>
                    </div>

                    {!isPlaying ? (
                            <button className="play-stop-button" onClick={startPlayback}>Play</button>
                        )
                        :
                        (
                            <button className="play-stop-button" onClick={pausePlayback}>Pause</button>
                        )
                    }


                    <p>
                        Step {currentStepIndex + 1} of {steps.length}
                    </p>
                </>
            )}
        </div>
    )
        ;
}

export default App;
