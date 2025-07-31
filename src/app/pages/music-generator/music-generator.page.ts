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
    if (!mp3Url) {
      console.error('Empty MP3 URL provided');
      this.showAudioErrorToast();
      return;
    }

    if (this.audioPlayer) {
      this.audioPlayer.stop();
      this.audioPlayer.unload();
      this.audioPlayer = null;
    }

    const fullUrl = this.musicGeneratorService.getFileUrl(mp3Url);
    console.log('Loading audio from URL:', fullUrl);
    
    // First verify the audio file is accessible with full content check
    console.log('Checking audio file availability...');
    fetch(fullUrl, { method: 'GET', cache: 'no-cache' })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        // Check for content length
        const contentLength = response.headers.get('content-length');
        const contentType = response.headers.get('content-type');
        
        console.log('Audio file fetch successful:', {
          status: response.status,
          statusText: response.statusText,
          contentType: contentType,
          contentLength: contentLength
        });
        
        // Verify we have an audio file with content
        if (!contentType?.includes('audio') && !contentType?.includes('mpeg')) {
          console.warn('Response may not be audio:', contentType);
        }
        
        if (!contentLength || parseInt(contentLength) < 1000) {
          console.warn('Audio file may be too small:', contentLength);
        }
        
        // Now that we've confirmed the file is accessible, create the audio player
        this.createAudioPlayer(fullUrl);
        
        // Show success message for fetch
        this.toastCtrl.create({
          message: 'Audio file found. Preparing playback...',
          duration: 2000,
          position: 'bottom',
          color: 'success'
        }).then(toast => toast.present());
      })
      .catch(error => {
        console.error('Audio file fetch error:', error);
        this.showAudioErrorToast();
      });
  }
  
  createAudioPlayer(fullUrl: string) {
    // Check browser audio support
    try {
      const testAudio = new Audio();
      const mp3Support = testAudio.canPlayType('audio/mpeg') || 'no';
      console.log('Browser audio support check:', {
        mp3: mp3Support,
        wav: testAudio.canPlayType('audio/wav') || 'no',
        ogg: testAudio.canPlayType('audio/ogg') || 'no'
      });
      
      if (mp3Support === 'no') {
        console.warn('Browser does not support MP3 format');
      }
    } catch (e) {
      console.error('Audio support test failed:', e);
    }

    // Create Howler instance with improved settings
    this.audioPlayer = new Howl({
      src: [fullUrl],
      html5: true, // Force HTML5 Audio for better compatibility
      format: ['mp3'],
      preload: true,
      volume: 1.0,
      autoplay: false, // Don't autoplay, let user click play button
      pool: 1, // Reduce the number of simultaneous connections
      onend: () => {
        console.log('Audio playback ended');
        this.isPlaying = false;
      },
      onload: () => {
        console.log('Audio loaded successfully');
        // Show success message
        this.toastCtrl.create({
          message: 'Audio loaded successfully. Press play to listen.',
          duration: 2000,
          position: 'bottom',
          color: 'success'
        }).then(toast => toast.present());
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
        this.tryNativeAudioFallback(fullUrl);
      },
      onplayerror: (id, error) => {
        console.error('Error playing audio with Howler:', error);
        this.tryNativeAudioFallback(fullUrl);
      }
    });
  }
  
  tryNativeAudioFallback(fullUrl: string) {
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
  }
  
  // Helper method to show audio error toast
  private showAudioErrorToast() {
    this.toastCtrl.create({
      message: 'Unable to play audio. This may be due to browser MP3 support or network issues. You can download the MIDI file instead.',
      duration: 5000,
      position: 'bottom',
      color: 'danger',
      buttons: [{
        text: 'Download MIDI',
        handler: () => {
          if (this.generatedExercise?.midi_url) {
            this.downloadMidi();
          }
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