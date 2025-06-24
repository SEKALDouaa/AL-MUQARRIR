import {
  Component,
  OnInit,
  OnDestroy,
  ElementRef,
  ViewChild,
  AfterViewInit,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { TranscriptionService } from '../../services/transcription/transcription.service';
import { ActivatedRoute } from '@angular/router';

interface TranscriptionSegment {
  speaker: string;
  text: string;
  timestamp?: number;
}

interface AudioConfig {
  sampleRate: number;
  channelCount: number;
  echoCancellation: boolean;
  noiseSuppression: boolean;
}

@Component({
  selector: 'app-realtime-transcription',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './realtime-transcription.component.html',
  styleUrls: ['./realtime-transcription.component.css'],
})
export class RealtimeTranscriptionComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('visualizer', { static: true }) visualizerRef!: ElementRef;

  // Public properties for template
  isRecording = false;
  isPaused = false; // Track if paused
  status = 'Ready to record';
  statusClass = '';
  transcriptionResults: TranscriptionSegment[] = [];

  // Private properties
  private mediaRecorder: MediaRecorder | null = null;
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private audioChunks: Blob[] = [];
  private chunkInterval: NodeJS.Timeout | null = null;
  private visualizerBars: HTMLElement[] = [];
  private animationFrame: number | null = null;

  // Configuration
  private readonly CHUNK_DURATION = 10000; // 10 seconds
  private readonly VISUALIZER_BARS = 50;
  private readonly AUDIO_CONFIG: AudioConfig = {
    sampleRate: 16000,
    channelCount: 1,
    echoCancellation: true,
    noiseSuppression: true,
  };

  // API configuration
  ngrokUrl = '';
  pvId: string | null = null;
  private API_URL = '';

  constructor(
    private transcriptionService: TranscriptionService,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    this.initializeComponent();
  }

  ngOnDestroy(): void {
    this.cleanup();
  }

  // 5. Add ngAfterViewInit to create visualizer after view is ready
  ngAfterViewInit(): void {
    // Create visualizer after view is fully initialized
    setTimeout(() => {
      this.createVisualizer();
    }, 100);
  }

  // Public methods
  async startRecording(): Promise<void> {
    try {
      if (this.isPaused && this.mediaRecorder) {
        // Resume recording
        this.isRecording = true;
        this.isPaused = false;
        this.mediaRecorder.start();
        this.startChunkInterval();

        // Ensure visualizer is ready before starting
        if (this.visualizerBars.length === 0) {
          this.createVisualizer();
        }
        setTimeout(() => this.startVisualizer(), 100);

        this.updateStatus('Recording...', 'recording');
        return;
      }

      this.updateStatus('Initializing...', '');

      const stream = await this.getUserMediaStream();
      await this.setupAudioProcessing(stream);
      this.setupMediaRecorder(stream);

      // Ensure visualizer is created before starting recording
      if (this.visualizerBars.length === 0) {
        this.createVisualizer();
      }

      this.startRecordingProcess();
      this.updateStatus('Recording...', 'recording');
    } catch (error: any) {
      this.handleError('Failed to start recording', error);
    }
  }

  stopRecording(): void {
    if (!this.isRecording) return;
    this.isRecording = false;
    this.isPaused = true;
    this.stopMediaRecorder();
    this.stopChunkInterval();
    this.stopVisualizer();
    this.closeAudioContext();
    this.updateStatus('Recording paused', '');
    // No backend update here
  }

  // Private initialization methods
  private initializeComponent(): void {
    this.pvId = this.route.snapshot.paramMap.get('id');
    this.fetchApiConfiguration();
  }

  private fetchApiConfiguration(): void {
    this.transcriptionService.getNgrokUrl().subscribe({
      next: (response) => {
        this.ngrokUrl = response.ngrok_url;
        this.API_URL = `${this.ngrokUrl}/process_audio_minimal_no_refine`;
        this.updateStatus('Ready to record', '');
      },
      error: (error) => {
        this.handleError('Failed to fetch API configuration', error);
      },
    });
  }

  // Audio setup methods
  private async getUserMediaStream(): Promise<MediaStream> {
    return await navigator.mediaDevices.getUserMedia({
      audio: this.AUDIO_CONFIG,
    });
  }

  private async setupAudioProcessing(stream: MediaStream): Promise<void> {
    try {
      this.audioContext = new (window.AudioContext ||
        (window as any).webkitAudioContext)();

      // Resume audio context if it's suspended (required by some browsers)
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume();
      }

      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 512; // Increased for better frequency resolution
      this.analyser.smoothingTimeConstant = 0.8;
      this.analyser.minDecibels = -90;
      this.analyser.maxDecibels = -10;

      const source = this.audioContext.createMediaStreamSource(stream);
      source.connect(this.analyser);

      console.log('Audio processing setup complete');
    } catch (error) {
      console.error('Failed to setup audio processing:', error);
      throw error;
    }
  }

  private setupMediaRecorder(stream: MediaStream): void {
    const options = {
      mimeType: 'audio/webm;codecs=opus',
    };

    this.mediaRecorder = new MediaRecorder(stream, options);
    this.audioChunks = [];

    this.mediaRecorder.ondataavailable = (event: BlobEvent) => {
      if (event.data.size > 0) {
        this.audioChunks.push(event.data);
      }
    };

    this.mediaRecorder.onstop = () => {
      this.processAudioChunk();
    };
  }

  // Recording control methods
  private startRecordingProcess(): void {
    if (!this.mediaRecorder) return;

    this.mediaRecorder.start();
    this.isRecording = true;
    this.startVisualizer();
    this.startChunkInterval();
  }

  private stopRecordingProcess(): void {
    this.isRecording = false;
    this.stopMediaRecorder();
    this.stopChunkInterval();
    this.stopVisualizer();
    this.closeAudioContext();
  }

  private stopMediaRecorder(): void {
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      this.mediaRecorder.stop();
      this.mediaRecorder.stream.getTracks().forEach((track) => track.stop());
      this.mediaRecorder = null;
    }
  }

  private startChunkInterval(): void {
    this.chunkInterval = setInterval(() => {
      if (this.isRecording && this.mediaRecorder) {
        this.mediaRecorder.stop();
        this.mediaRecorder.start();
      }
    }, this.CHUNK_DURATION);
  }

  private stopChunkInterval(): void {
    if (this.chunkInterval) {
      clearInterval(this.chunkInterval);
      this.chunkInterval = null;
    }
  }

  private closeAudioContext(): void {
    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
      this.analyser = null;
    }
  }

  // Audio processing methods
  private async processAudioChunk(): Promise<void> {
    if (this.audioChunks.length === 0) return;

    try {
      const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
      this.audioChunks = [];

      const wavBlob = await this.convertToWav(audioBlob);
      const base64Audio = await this.blobToBase64(wavBlob);

      await this.sendToTranscriptionAPI(base64Audio);
    } catch (error: any) {
      this.handleError('Audio processing failed', error);
    }
  }

  private async convertToWav(webmBlob: Blob): Promise<Blob> {
    const arrayBuffer = await webmBlob.arrayBuffer();
    const offlineCtx = new OfflineAudioContext(1, 44100, 44100);
    const audioBuffer = await offlineCtx.decodeAudioData(arrayBuffer);
    const wavBuffer = this.audioBufferToWav(audioBuffer);

    return new Blob([wavBuffer], { type: 'audio/wav' });
  }

  private audioBufferToWav(buffer: AudioBuffer): ArrayBuffer {
    const length = buffer.length;
    const arrayBuffer = new ArrayBuffer(44 + length * 2);
    const view = new DataView(arrayBuffer);

    // WAV header
    const writeString = (offset: number, str: string) => {
      for (let i = 0; i < str.length; i++) {
        view.setUint8(offset + i, str.charCodeAt(i));
      }
    };

    writeString(0, 'RIFF');
    view.setUint32(4, 36 + length * 2, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, buffer.sampleRate, true);
    view.setUint32(28, buffer.sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(36, 'data');
    view.setUint32(40, length * 2, true);

    // Convert samples
    const samples = buffer.getChannelData(0);
    let offset = 44;
    for (let i = 0; i < length; i++) {
      const sample = Math.max(-1, Math.min(1, samples[i]));
      view.setInt16(offset, sample * 0x7fff, true);
      offset += 2;
    }

    return arrayBuffer;
  }

  private blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const base64 = (reader.result as string).split(',')[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  // API communication methods
  private async sendToTranscriptionAPI(base64Audio: string): Promise<void> {
    try {
      const response = await fetch(this.API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({ audio_data_base64: base64Audio }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `HTTP ${response.status}: ${response.statusText} - ${errorText}`
        );
      }

      const result = await response.json();
      this.handleTranscriptionResult(result.result);
    } catch (error: any) {
      this.handleError('API request failed', error);
    }
  }

  private handleTranscriptionResult(result: any): void {
    if (!result || result.length === 0) return;

    // Preprocessing: assign incrementing UNKNOWN i for unknown speakers
    let unknownCounter = this.transcriptionResults.filter((seg) =>
      seg.speaker.startsWith('UNKNOWN')
    ).length;
    const unknownSpeakerMap = new Map<string, string>();

    result.forEach((item: any) => {
      let speaker = Object.keys(item)[0];
      const text = item[speaker];

      // Check for unknown speaker patterns
      if (
        speaker.startsWith('No speaker found for:') ||
        speaker.trim().toUpperCase() === 'UNKNOWN'
      ) {
        // If this exact unknown speaker hasn't been mapped yet in this batch, assign a new UNKNOWN i
        if (!unknownSpeakerMap.has(speaker)) {
          unknownCounter += 1;
          unknownSpeakerMap.set(speaker, `UNKNOWN ${unknownCounter}`);
        }
        speaker = unknownSpeakerMap.get(speaker)!;
      }

      if (text && text.trim()) {
        this.transcriptionResults.push({
          speaker,
          text: text.trim(),
          timestamp: Date.now(),
        });
      }
    });

    this.scrollToLatestTranscription();
  }

  private scrollToLatestTranscription(): void {
    setTimeout(() => {
      const container = document.getElementById('transcriptionResults');
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    }, 100);
  }

  // Visualizer methods
  private createVisualizer(): void {
    const visualizer = this.visualizerRef?.nativeElement as HTMLElement;
    if (!visualizer) {
      console.error('Visualizer element not found');
      return;
    }

    // Clear existing content
    visualizer.innerHTML = '<div class="visualizer-bg"></div>';
    this.visualizerBars = [];

    const containerWidth = visualizer.offsetWidth || 600;
    const barWidth = 6;
    const gap = Math.max(
      2,
      (containerWidth - this.VISUALIZER_BARS * barWidth) /
        (this.VISUALIZER_BARS - 1)
    );

    for (let i = 0; i < this.VISUALIZER_BARS; i++) {
      const bar = document.createElement('div');
      bar.className = 'wave-bar';
      bar.style.position = 'absolute';
      bar.style.width = `${barWidth}px`;
      bar.style.left = `${i * (barWidth + gap)}px`;
      bar.style.height = '2px';
      bar.style.bottom = '10px';
      bar.style.background = 'linear-gradient(to top, #4ade80, #7b3131 80%)';
      bar.style.borderRadius = '3px';
      bar.style.transition = 'height 0.15s ease';
      bar.style.boxShadow = '0 0 10px rgba(74, 222, 128, 0.3)';
      bar.style.zIndex = '1';

      visualizer.appendChild(bar);
      this.visualizerBars.push(bar);
    }

    console.log(`Created ${this.visualizerBars.length} visualizer bars`);
  }

  private startVisualizer(): void {
    if (!this.analyser) return;
    this.updateVisualizer();
  }

  private updateVisualizer(): void {
    if (
      !this.analyser ||
      !this.isRecording ||
      this.visualizerBars.length === 0 // Fixed typo: was visualizerBards
    ) {
      return;
    }

    const bufferLength = this.analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    this.analyser.getByteFrequencyData(dataArray);

    // Use different frequency ranges for more dynamic visualization
    this.visualizerBars.forEach((bar, index) => {
      // Map bars to different frequency ranges
      const freqIndex = Math.floor(
        (index / this.VISUALIZER_BARS) * bufferLength
      );
      const value = dataArray[freqIndex] || 0;

      // Apply logarithmic scaling for better visual effect
      const normalizedValue = value / 255;
      const height = Math.max(2, Math.pow(normalizedValue, 0.5) * 100);

      bar.style.height = `${height}px`;

      // Add color variation based on intensity
      if (height > 50) {
        bar.style.background = 'linear-gradient(to top, #4ade80, #22c55e)';
        bar.style.boxShadow = '0 0 15px rgba(74, 222, 128, 0.6)';
      } else if (height > 20) {
        bar.style.background = 'linear-gradient(to top, #4ade80, #7b3131 80%)';
        bar.style.boxShadow = '0 0 10px rgba(74, 222, 128, 0.3)';
      } else {
        bar.style.background = 'linear-gradient(to top, #7b3131, #5a2424)';
        bar.style.boxShadow = '0 0 5px rgba(123, 49, 49, 0.2)';
      }
    });

    if (this.isRecording) {
      this.animationFrame = requestAnimationFrame(() =>
        this.updateVisualizer()
      );
    }
  }

  private stopVisualizer(): void {
    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame);
      this.animationFrame = null;
    }
    this.visualizerBars.forEach((bar) => {
      bar.style.height = '2px';
    });
  }

  // Utility methods
  private updateStatus(message: string, className: string): void {
    this.status = message;
    this.statusClass = className;
  }

  private handleError(message: string, error: any): void {
    console.error(message, error);
    this.updateStatus(
      `${message}: ${error.message || 'Unknown error'}`,
      'error'
    );
  }

  private cleanup(): void {
    this.stopRecordingProcess();

    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame);
    }

    this.transcriptionResults = [];
    this.visualizerBars = [];
  }

  // Add navigation to assign speakers
  goToAssignSpeakers() {
    if (this.pvId && this.transcriptionResults.length) {
      // Prepare segments for backend update
      const segments = this.transcriptionResults.map(seg => ({ speaker: seg.speaker, text: seg.text }));
      this.transcriptionService.updateTranscription(Number(this.pvId), { Transcription: segments }).subscribe({
        next: () => {
          window.location.href = `/Home/pv/${this.pvId}/assign-speakers`;
        },
        error: (err) => {
          this.handleError('Échec de la mise à jour de la transcription', err);
        }
      });
    } else if (this.pvId) {
      window.location.href = `/Home/pv/${this.pvId}/assign-speakers`;
    }
  }

  // Public utility methods for template
  getTranscriptionCount(): number {
    return this.transcriptionResults.length;
  }

  getRecordingButtonLabel(): string {
    if (this.isRecording) return 'Enregistrement...';
    if (this.isPaused && this.transcriptionResults.length > 0)
      return 'Reprendre l\'enregistrement';
    return 'Démarrer l\'enregistrement';
  }

  clearTranscription(): void {
    this.transcriptionResults = [];
  }

  downloadTranscription(): void {
    if (this.transcriptionResults.length === 0) return;

    const content = this.transcriptionResults
      .map(
        (segment, index) => `${index + 1}. ${segment.speaker}: ${segment.text}`
      )
      .join('\n\n');

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');

    a.href = url;
    a.download = `transcription-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    URL.revokeObjectURL(url);
  }
}
