import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface ExerciseRequest {
  instrument: string;
  level: string;
  key: string;
  tempo: number;
  time_signature: string;
  measures: number;
  custom_prompt?: string;
  mode: 'Exercise Parameters' | 'Exercise Prompt';
}

export interface ExerciseResponse {
  exercise: Array<{
    note: string;
    duration: number;
    cumulative_duration: number;
  }>;
  tempo: string;
  duration: string;
  time_signature: string;
  total_duration: number;
  mp3_url: string;
  midi_url: string;
}

export interface ChatRequest {
  message: string;
  history: Array<[string, string]>;
  instrument: string;
  level: string;
}

export interface ChatResponse {
  history: Array<[string, string]>;
}

@Injectable({
  providedIn: 'root'
})
export class MusicGeneratorService {
  private apiUrl = environment.musicGeneratorApiUrl || 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  /**
   * Generate a music exercise based on the provided parameters
   */
  generateExercise(request: ExerciseRequest): Observable<ExerciseResponse> {
    return this.http.post<ExerciseResponse>(`${this.apiUrl}/generate`, request);
  }

  /**
   * Get the full URL for an MP3 or MIDI file
   */
  getFileUrl(relativeUrl: string): string {
    // If the URL is empty or null, return empty string
    if (!relativeUrl) {
      console.warn('Empty URL provided');
      return '';
    }

    // If the URL is already absolute, return it as is
    if (relativeUrl.startsWith('http')) {
      console.log('Using absolute URL:', relativeUrl);
      return relativeUrl;
    }
    
    // Ensure the relative URL starts with a slash
    const normalizedRelativeUrl = relativeUrl.startsWith('/') ? relativeUrl : `/${relativeUrl}`;
    
    // Ensure the API URL doesn't end with a slash to avoid double slashes
    const normalizedApiUrl = this.apiUrl.endsWith('/') ? this.apiUrl.slice(0, -1) : this.apiUrl;
    
    const fullUrl = `${normalizedApiUrl}${normalizedRelativeUrl}`;
    console.log('Constructed full URL:', fullUrl);
    return fullUrl;
  }

  /**
   * Chat with the AI music teacher
   */
  chat(request: ChatRequest): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.apiUrl}/chat`, request);
  }
}