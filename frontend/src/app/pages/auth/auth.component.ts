import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { HttpClientModule, HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth/auth.service';
import { ToastrService } from 'ngx-toastr';

@Component({
selector: 'app-auth',
standalone: true,
imports: [
CommonModule,
ReactiveFormsModule,
HttpClientModule,
],
templateUrl: './auth.component.html',
styleUrls: ['./auth.component.scss']
})
export class AuthComponent {
isRegisterMode = false;
birthDateFocused = false;
currentLang = 'FR';
loginMode: boolean = true;

loginForm: FormGroup;
registerForm: FormGroup;

constructor(
    private fb: FormBuilder,
    private router: Router,
    private http: HttpClient,
    private toastr: ToastrService,
    private authService: AuthService
  ) {
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', Validators.required],
    });

    this.registerForm = this.fb.group({
      prenom: ['', Validators.required],
      nom: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      password: ['', Validators.required],
      numeroTel: ['', Validators.required],
      dateNaissance: ['', Validators.required],
    });
  }

  toggleMode() {
    this.isRegisterMode = !this.isRegisterMode;
  }

  onLogin() {
    this.authService.login(this.loginForm.value).subscribe({
      next: (res) => {
        localStorage.setItem('access_token', res.access_token); // ✅ FIXED
        this.router.navigate(['/Home']);
      },
      error: (err) => {
        this.toastr.error(err.error?.error || 'Login failed');
      }
    });
  }

  onRegister() {
    this.authService.register(this.registerForm.value).subscribe({
      next: () => {
        this.toastr.success('Account created successfully!');
        this.loginMode = true;
      },
      error: (err) => {
        this.toastr.error(err.error?.error || 'Signup failed');
      }
    });
  }
    setLang(lang: string) {
    this.currentLang = lang;
  }

  onBlurDate() {
    this.birthDateFocused = false;
  }

}
