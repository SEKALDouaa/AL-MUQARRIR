import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { HttpClientModule, HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { RouterModule } from '@angular/router';

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

loginForm: FormGroup;
registerForm: FormGroup;

toastMessages: { type: string; text: string }[] = [];

constructor(private fb: FormBuilder, private http: HttpClient, private router: Router) {
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', Validators.required],
    });

    this.registerForm = this.fb.group({
      first_name: ['', Validators.required],
      last_name: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      password: ['', Validators.required],
      phone_number: ['', Validators.required],
      date_of_birth: ['', Validators.required],
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
  if (this.loginForm.invalid) return;

  // Directly navigate without HTTP request
  this.router.navigate(['/']);
  }


  onRegister() {
    if (this.registerForm.invalid) return;

    this.http.post('/signup', this.registerForm.value).subscribe({
      next: () => {
        this.showToast('success', 'Account created successfully. Please login.');
        this.toggleMode();
      },
      error: (err) => {
        this.showToast('error', err.error?.error || 'Signup failed');
      }
    });
  }

  showToast(type: string, text: string) {
    this.toastMessages.push({ type, text });
    setTimeout(() => this.toastMessages.shift(), 3000);
  }
}
