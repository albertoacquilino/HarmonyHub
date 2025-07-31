import { Component, OnInit } from '@angular/core';
import { MusicGeneratorService, ExerciseRequest, ExerciseResponse } from '../../services/music-generator.service';
import { LoadingController, ToastController, IonicModule } from '@ionic/angular';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Howl } from 'howler';

@Component({
  selector: 'app-music-generator',
  templateUrl: './music-generator.page.html',
  styleUrls: ['./music-generator.page.scss'],
  standalone: true,
  imports: [IonicModule, CommonModule, FormsModule]
})
export class MusicGeneratorPage implements OnInit {
  // Generation parameters
  generationMode: 'Exercise Parameters' | 'Exercise Prompt' = 'Exercise Parameters';
  instruments: string[] = ['Trumpet', 'Piano', 'Violin', 'Clarinet', 'Flute'];
  levels: string[] = ['Beginner', 'Intermediate', 'Advanced'];
  keys: string[] = ['C Major', 'G Major', 'D Major', 'F Major', 'Bb Major', 'A Minor', 'E Minor'];
  timeSignatures: string[] = ['3/4', '4/4'];
  measureOptions: number[] = [4, 8];
  
  // Selected values
  selectedInstrument: string = 'Trumpet';
  selectedLevel: string = 'Intermediate';
  selectedKey: string = 'C Major';
  selectedTimeSignature: string = '4/4';
  selectedMeasures: number = 4;
  customPrompt: string = '';
  
  // Results
  generatedExercise: ExerciseResponse | null = null;
  audioPlayer: Howl | null = null;
  isPlaying: boolean = false;
  
  // Chat
  chatHistory: Array<[string, string]> = [];
  chatMessage: string = '';

  constructor(
    private musicGeneratorService: MusicGeneratorService,
    private loadingCtrl: LoadingController,
    private toastCtrl: ToastController
  ) {}

  ngOnInit() {}

  async generateExercise() {
    const loading = await this.loadingCtrl.create({
      message: 'Generating music exercise...',
    });
    await loading.present();

    try {
      const request: ExerciseRequest = {
        instrument: this.selectedInstrument,
        level: this.selectedLevel,
        key: this.selectedKey,
        tempo: 60, // Fixed tempo
        time_signature: this.selectedTimeSignature,
        measures: this.selectedMeasures,
        custom_prompt: this.customPrompt,
        mode: this.generationMode
      };

      this.musicGeneratorService.generateExercise(request).subscribe(
        (response: ExerciseResponse) => {
          this.generatedExercise = response;
          this.loadAudio(response.mp3_url);
          loading.dismiss();
        },
        async (error: any) => {
          console.error('Error generating exercise:', error);
          loading.dismiss();
          const toast = await this.toastCtrl.create({
            message: 'Failed to generate exercise. Please try again.',
            duration: 3000,
            position: 'bottom',
            color: 'danger'
          });
          toast.present();
        }
      );
    } catch (error) {
      console.error('Error in generate exercise:', error);
      loading.dismiss();
    }
  }

  loadAudio(mp3Url: string) {
    if (this.audioPlayer) {
      this.audioPlayer.stop();
      this.audioPlayer.unload();
      this.audioPlayer = null;
    }

    const fullUrl = this.musicGeneratorService.getFileUrl(mp3Url);
    console.log('Loading audio from URL:', fullUrl);
    
    // Try to fetch the audio file directly to check if it's accessible
    fetch(fullUrl, { method: 'HEAD' })
      .then(response => {
        console.log('Audio file fetch check:', {
          status: response.status,
          statusText: response.statusText,
          contentType: response.headers.get('content-type'),
          contentLength: response.headers.get('content-length')
        });
      })
      .catch(error => {
        console.error('Audio file fetch error:', error);
      });

    
    // Try to create a test audio element to check browser audio support
    try {
      const testAudio = new Audio();
      console.log('Browser audio support check:', {
        mp3: testAudio.canPlayType('audio/mpeg') || 'no',
        wav: testAudio.canPlayType('audio/wav') || 'no',
        ogg: testAudio.canPlayType('audio/ogg') || 'no'
      });
    } catch (e) {
      console.error('Audio support test failed:', e);
    }

    // Try to fetch the audio file directly to check if it's accessible
    fetch(fullUrl, { method: 'HEAD' })
      .then(response => {
        console.log('Audio file fetch check:', {
          status: response.status,
          statusText: response.statusText,
          contentType: response.headers.get('content-type'),
          contentLength: response.headers.get('content-length')
        });
      })
      .catch(error => {
        console.error('Audio file fetch error:', error);
      });

    // Try with Howler
    this.audioPlayer = new Howl({
      src: [fullUrl],
      html5: true, // Force HTML5 Audio to avoid Flash
      format: ['mp3'],
      preload: true,
      volume: 1.0,
      autoplay: false, // Don't autoplay until we're sure it's loaded
      onend: () => {
        console.log('Audio playback ended');
        this.isPlaying = false;
      },
      onload: () => {
        console.log('Audio loaded successfully');
        // Don't autoplay, let user click play button
      },
      onloaderror: (id, error) => {
        console.error('Error loading audio with Howler:', error);
        
        // Show error to user
        this.toastCtrl.create({
          message: 'Error loading audio. Trying alternative method...',
          duration: 3000,
          position: 'bottom',
          color: 'warning'
        }).then(toast => toast.present());
        
        // Fallback to native Audio API
        console.log('Trying fallback to native Audio API');
        const nativeAudio = new Audio();
        
        nativeAudio.addEventListener('canplaythrough', () => {
          console.log('Native audio can play through');
          nativeAudio.play()
            .then(() => {
              console.log('Native audio playing successfully');
              this.isPlaying = true;
            })
            .catch(e => {
              console.error('Native audio play error:', e);
              this.showAudioErrorToast();
            });
        });
        
        nativeAudio.addEventListener('error', (e) => {
          console.error('Native audio error:', e);
          this.showAudioErrorToast();
        });
        
        nativeAudio.src = fullUrl;
        nativeAudio.load();
      },
      onplayerror: (id, error) => {
        console.error('Error playing audio with Howler:', error);
        this.showAudioErrorToast();
      }
    });
  }
  
  // Helper method to show audio error toast
  private showAudioErrorToast() {
    this.toastCtrl.create({
      message: 'Unable to play audio. Your browser may not support MP3 playback or there might be a network issue. You can download the MIDI file instead.',
      duration: 5000,
      position: 'bottom',
      color: 'danger',
      buttons: [{
        text: 'Download MIDI',
        handler: () => {
          this.downloadMidi();
        }
      }]
    }).then(toast => toast.present());
  }

  playAudio() {
    if (this.audioPlayer) {
      console.log('Playing audio');
      this.audioPlayer.play();
      this.isPlaying = true;
    }
  }

  pauseAudio() {
    if (this.audioPlayer) {
      console.log('Pausing audio');
      this.audioPlayer.pause();
      this.isPlaying = false;
    }
  }

  downloadMidi() {
    if (this.generatedExercise) {
      const fullUrl = this.musicGeneratorService.getFileUrl(this.generatedExercise.midi_url);
      window.open(fullUrl, '_blank');
    }
  }

  sendChatMessage() {
    if (!this.chatMessage.trim()) return;

    const request = {
      message: this.chatMessage,
      history: this.chatHistory,
      instrument: this.selectedInstrument,
      level: this.selectedLevel
    };

    // Add user message to chat immediately
    this.chatHistory.push([this.chatMessage, '...']);
    const tempMessage = this.chatMessage;
    this.chatMessage = '';

    this.musicGeneratorService.chat(request).subscribe(
      (response: {history: Array<[string, string]>}) => {
        // Update chat history with response
        this.chatHistory = response.history;
      },
      (error: any) => {
        console.error('Chat error:', error);
        // Update the last message to show error
        const lastIndex = this.chatHistory.length - 1;
        if (lastIndex >= 0 && this.chatHistory[lastIndex][0] === tempMessage) {
          this.chatHistory[lastIndex][1] = 'Error: Failed to get response';
        }
      }
    );
  }
}