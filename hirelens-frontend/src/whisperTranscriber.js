class WhisperTranscriber {
    constructor() {
        this.isLoaded = false;
        this.isLoading = false;
        this.model = null;
    }
    
    // Debug function to play recorded audio
    playAudio(audioBlob) {
        const audio = new Audio();
        const url = URL.createObjectURL(audioBlob);
        audio.src = url;
        audio.controls = true;
        
        console.log("Debug: Playing recorded audio to verify quality");
        document.body.appendChild(audio);
        audio.style.position = "fixed";
        audio.style.bottom = "10px";
        audio.style.right = "10px";
        audio.style.zIndex = "9999";
        
        audio.play().catch(e => console.error("Error playing audio:", e));
        
        return url;
    }
    
    async load() {
        if (this.isLoaded || this.isLoading) return;
        
        this.isLoading = true;
        console.log("Loading Whisper model...");
        
        try {
            // Configure the Transformers.js library
            const { pipeline, env } = await import('@xenova/transformers');
            
            // Configure model caching in IndexedDB (in browser storage)
            env.useBrowserCache = true;
            env.allowLocalModels = false; // Don't look for models in local filesystem
            env.useCustomCache = true; // Use custom cache location 
            env.cacheDir = "hf-models"; // Store in IndexedDB with this name
            
            console.log("Downloading and initializing Whisper model - this may take a moment on first run");
            
            // Load the whisper model - using tiny.en for English-only for better results
            this.model = await pipeline(
                'automatic-speech-recognition', 
                'Xenova/whisper-tiny.en',
                { 
                    progress_callback: (progress) => {
                        if (progress.progress) {
                            console.log(`Model loading: ${Math.round(progress.progress * 100)}%`);
                        }
                    },
                    chunk_length_s: 30,
                    return_timestamps: false
                }
            );
            
            this.isLoaded = true;
            this.isLoading = false;
            console.log("Whisper model loaded successfully");
        } catch (error) {
            this.isLoading = false;
            console.error("Error loading Whisper model:", error);
            throw error;
        }
    }
    
    async transcribeAudio(audioBlob) {
        // Make sure model is loaded
        if (!this.isLoaded) {
            try {
                await this.load();
            } catch (error) {
                console.error("Failed to load Whisper model:", error);
                return "Failed to load speech recognition model. Using fallback method.";
            }
        }
        
        if (!this.model) {
            console.error("Model not available for transcription");
            return "Speech recognition model unavailable. Please try again.";
        }
        
        console.log(`Transcribing audio (${audioBlob.size} bytes)...`);
        
        try {
            // Debug: Check audio blob type and content
            console.log("Audio MIME type:", audioBlob.type);
            
            // Create a URL for the blob and play it to verify quality
            const audioUrl = this.playAudio(audioBlob);
            
            // Try to convert to WAV format if possible
            let processBlob = audioBlob;
            
            // Transcribe the audio with more specific options
            const result = await this.model(processBlob, {
                sampling_rate: 16000, // Explicitly set sample rate
                chunk_length_s: 30,
                stride_length_s: 5,
                task: "transcribe", 
                language: "en",
                return_timestamps: false
            });
            
            console.log("Transcription complete. Raw result:", result);
            
            const transcription = result.text || "";
            
            if (transcription.trim() === "") {
                console.log("Empty transcription returned - no speech detected");
                return "No speech detected. Please speak louder or check your microphone.";
            }
            
            console.log("Transcription complete:", transcription);
            return transcription;
        } catch (error) {
            console.error("Error transcribing audio:", error);
            return `Error transcribing audio: ${error.message}. Please try again.`;
        }
    }
}

// Create a single instance to be used across the app
const transcriber = new WhisperTranscriber();
export default transcriber; 