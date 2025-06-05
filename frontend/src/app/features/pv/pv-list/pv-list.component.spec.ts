import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PvListComponent } from './pv-list.component';

describe('PvListComponent', () => {
  let component: PvListComponent;
  let fixture: ComponentFixture<PvListComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PvListComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PvListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
