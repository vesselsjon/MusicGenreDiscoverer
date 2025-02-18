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

  constructor(private musicGenreDiscovererService: MusicGenreDiscovererService) {}

  public ngOnInit(): void {
    this.musicGenreDiscovererService.GetData().subscribe({
      next: (data) => {
        console.log(data)
      }, error: (err) => {
        console.error(err);
      }
    });
  }
}
