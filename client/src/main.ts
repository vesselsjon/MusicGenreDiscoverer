import { platformBrowserDynamic } from '@angular/platform-browser-dynamic';
import { AppModule } from './app/app.module';

export function getBaseUrl(): string {
  const baseElement = document.getElementsByTagName('base')[0];
  let baseUrl = baseElement ? baseElement.href : '';

  // Override base URL in local development
  if (baseUrl.includes('localhost:4200')) {
    baseUrl = 'http://localhost:8080/';
  }

  return 'https://musicgenrediscoverer.onrender.com/';
}

const providers: any = [
  { provide: 'BASE_URL', useFactory: getBaseUrl, deps: [] },
];

platformBrowserDynamic(providers).bootstrapModule(AppModule, {
  ngZoneEventCoalescing: true
})
  .catch(err => console.error(err));