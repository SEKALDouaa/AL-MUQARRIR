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

toastMessages: { type: string; text: string }[] = [];

constructor(  private fb: FormBuilder,
              private router: Router,
              private http: HttpClient,
              private toastr: ToastrService,
              private authService: AuthService) {
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

  setLang(lang: string) {
    if (this.currentLang !== lang) {
      this.currentLang = lang;
      // TODO: Add your language switch logic here
    }
  }

  toggleMode() {
    this.isRegisterMode = !this.isRegisterMode;
  }

  onBlurDate() {
    if (!this.registerForm.value.date_of_birth) {
      this.birthDateFocused = false;
    }
  }

  onLogin() {
    this.authService.login(this.loginForm.value).subscribe({
      next: (res) => {
        localStorage.setItem('token', res.access_token);
        this.router.navigate(['/Home']);
      },
      error: (err) => {
        this.showToast('error', err.error?.error || 'Login failed');
      }
    });
  }


  onRegister() {
    this.authService.register(this.registerForm.value).subscribe({
      next: () => {
        this.showToast('success', 'Account created successfully!');
        this.loginMode = true;
      },
      error: (err) => {
        this.showToast('error', err.error?.error || 'Signup failed');
      }
    });
  }

  showToast(type: string, text: string) {
  if (type === 'success') {
    this.toastr.success(text);
  } else if (type === 'error') {
    this.toastr.error(text);
  }
}
}
