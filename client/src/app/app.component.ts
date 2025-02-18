import { Component, OnInit } from '@angular/core';
import { MusicGenreDiscovererService } from './services/music-genre-discoverer.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  standalone: false,
  styleUrl: './app.component.scss'
})
export class AppComponent implements OnInit {
  title = 'client';
  recommendations: any[] = [];

  constructor(private musicGenreDiscovererService: MusicGenreDiscovererService) {}

  public ngOnInit(): void {
    const userId = 2;  // Example user ID, you can get it dynamically
    this.musicGenreDiscovererService.GetRecommendations(userId).subscribe({
      next: (data) => {
        this.recommendations = data;
        console.log(this.recommendations);
      },
      error: (err) => {
        console.error(err);
      }
    });
  }
}
