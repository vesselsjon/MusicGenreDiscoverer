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
        this._apiUrl = Location.joinWithSlash(baseUrl, '/api');
    }

    public GetData(): Observable<Object> {
        return this.http.get(Location.joinWithSlash(this._apiUrl, 'users')) as Observable<Object>;
    }
}