import { Location } from "@angular/common";
import { HttpClient } from "@angular/common/http";
import { Inject, Injectable } from "@angular/core";
import { Observable } from "rxjs";

@Injectable({
    providedIn: 'root',
})
export class MusicGenreDiscovererService {
    //#region Inputs, Outputs, ViewChilds
    //#endregion Inputs, Outputs, ViewChilds

    //#region Public Variables
    //#endregion Public Variables

    //#region Private Variables
    private _apiUrl: string;
    //#endregion Private Variables

    //#region Properties
    //#endregion Properties

    //#region Constructor and Angular Life Cycle
    constructor(private http: HttpClient, @Inject('BASE_URL') baseUrl: string) {
        this._apiUrl = Location.joinWithSlash(baseUrl, '/MusicGenreDiscoverer');
    }
    //#endregion Constructor and Angular Life Cycle

    //#region Event Handlers
    //#endregion Event Handlers

    //#region Public Methods
    public GetRecommendations(userId: number, n: number = 10): Observable<any> {
        const params = { user_id: userId, n: n };
        return this.http.get(Location.joinWithSlash(this._apiUrl, 'recommendations'), { params }) as Observable<any>;
    }

    public Upload(formData: FormData): Observable<any> {
        return this.http.post(Location.joinWithSlash(this._apiUrl, 'upload'), formData) as Observable<any>;
    }
    //#endregion Public Methods

    //#region Private Methods
    //#endregion Private Methods
}