import { HttpClient } from "@angular/common/http";
import { Inject, Injectable } from "@angular/core";
import { Location } from "@angular/common";
import { Observable } from "rxjs";

@Injectable({
    providedIn: 'root',
})
export class MusicGenreDiscovererService {
    private _apiUrl: string;

    constructor(private http: HttpClient, @Inject('BASE_URL') baseUrl: string) {
        this._apiUrl = Location.joinWithSlash(baseUrl, '/MusicGenreDiscoverer');
    }

    public GetRecommendations(userId: number, n: number = 10): Observable<any> {
        const params = { user_id: userId, n: n };
        return this.http.get(Location.joinWithSlash(this._apiUrl, 'recommendations'), { params }) as Observable<any>;
    }

    public Upload(formData: FormData): Observable<any> {
        return this.http.post(Location.joinWithSlash(this._apiUrl, 'upload'), formData) as Observable<any>;
    }
}