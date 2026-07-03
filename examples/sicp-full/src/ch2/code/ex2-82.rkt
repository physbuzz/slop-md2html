#lang sicp

(define (square x) (* x x))
;; ===================================================================
;; =========================== generic ops ===========================
;; ===================================================================
(define operation-table '())
(define coercion-table '()) ; Problems 2.81+

(define (assoc key records)
  (cond ((null? records) #f)
        ((equal? key (caar records)) (car records))
        (else (assoc key (cdr records)))))

(define (put op type-tags proc)
  (let ((op-list-entry (assoc op operation-table)))
    (if op-list-entry
        (let ((proc-list (cadr op-list-entry)))
           (let ((proc-pair-entry (assoc type-tags proc-list)))
             (if proc-pair-entry
                 (set-cdr! proc-pair-entry proc)
                 (set-car! (cdr op-list-entry)
                           (cons (cons type-tags proc) proc-list)))))
        (set! operation-table
              (cons (list op (list (cons type-tags proc)))
                    operation-table)))))

(define (get op type-tags)
  (let ((op-list-entry (assoc op operation-table)))
    (if op-list-entry
        (let ((proc-list (cadr op-list-entry)))
          (let ((proc-pair-entry (assoc type-tags proc-list)))
            (if proc-pair-entry
                (cdr proc-pair-entry)
                #f)))
        #f)))

;; Type coercion stuff for ex2-81 onwards.

;; Stores a procedure to convert from type1 to type2
(define (put-coercion type1 type2 proc)
  (let ((type1-entry (assoc type1 coercion-table)))
    (if type1-entry
        (let ((proc-list (cadr type1-entry)))
          (let ((type2-entry (assoc type2 proc-list)))
            (if type2-entry
                (set-cdr! type2-entry proc)
                (set-car! (cdr type1-entry)
                          (cons (cons type2 proc) proc-list)))))
        (set! coercion-table
              (cons (list type1 (list (cons type2 proc))) 
                    coercion-table)))))
(define (get-coercion type1 type2)
  (let ((type1-entry (assoc type1 coercion-table)))
    (if type1-entry
        (let ((proc-list (cadr type1-entry))) 
          (let ((type2-entry (assoc type2 proc-list)))
            (if type2-entry
                (cdr type2-entry)
                #f)))
        #f)))

;; Modified for ex2-78. 
(define (attach-tag type-tag contents)
  (if (equal? type-tag 'scheme-number) 
      contents
      (cons type-tag contents)))
(define (type-tag datum)
  (cond ((pair? datum) (car datum))
        ((number? datum) 'scheme-number)
        (else (error "Bad tagged datum: TYPE-TAG" datum))))
(define (contents datum)
  (cond ((pair? datum) (cdr datum))
        ((number? datum) datum)
        (else (error "Bad tagged datum: CONTENTS" datum))))




;; Try to coerce every element of args into target-type (a single type).
;; If a coercion fails to exist, or if the function on type (target-type
;; target-type ...) doesn't exist, return false.
(define (coerce-all target-type args) 
  ;; get the function f that coerces source-type to target-type if it 
  ;; exists, identity lambda if it's the same type, and false otherwise.
  (define (coerce-function source-type) 
    (let ((coercion (get-coercion source-type target-type)))
      (if coercion 
          coercion
          (if (eq? source-type target-type)
            (lambda (x) x)
            #f))))
        
  ;; Coerce all arguments if all type coercions exist, else return false.
  (define (map-if-exists procs args)
    (if (= (length procs) (length args))
      (if (null? procs) '() 
        (let ((coercion (car procs)) (x (car args)))
          (if coercion
              (let ((rest (map-if-exists (cdr procs) (cdr args))))
                (if rest 
                    (cons (coercion x) rest)
                    #f))
              #f)))
      (error "procs and args must be the same length inside coerce-all")))
  (let ((type-tags (map type-tag args)))
    (let ((procs (map coerce-function type-tags)))
      (map-if-exists procs args))))

(define (apply-generic op . args)
  ;; Attempt the coerction to the nth type. 
  ;; The car of the result will be false if no function and coercion exists
  ;; If one does exist, the car will be true and the cadr will be the result.
  (define (attempt-coercions n type-tags args)
    ;; So long as n<=length(type-tags) try to look up a function 
    ;; with type tags all of (list-ref type-tags n). If not, increase n by one
    ;; and try again.
    (if (< n (length type-tags))
      (let ((target-type (list-ref type-tags n)))
        (let ((proc (get op (map (lambda (x) target-type) type-tags)))
              (args-coerced (coerce-all target-type args)))
          (if (and proc args-coerced)
              (list #t (apply proc (map contents args-coerced)))
            (attempt-coercions (+ n 1) type-tags args))))
       (list #f )))
  (let ((type-tags (map type-tag args)))
    (let ((proc (get op type-tags)))
      (if proc
          (apply proc (map contents args))
          (if (> (length args) 1)
            (let ((res (attempt-coercions 0 type-tags args)))
              (if (car res)
                (cadr res)
                (error
                 "No method for these types!!!"
                 (list op type-tags))))
            (error
             "No method for these types"
             (list op type-tags)))))))

;; ===================================================================
;; ========================== Number package =========================
;; ===================================================================

(define (install-scheme-number-package)
  (define (tag x)
    (attach-tag 'scheme-number x))
  (put 'egu? '(scheme-number scheme-number) 
       (lambda (x y) (= x y))) ;Problem 2.79
  (put 'add '(scheme-number scheme-number)
       (lambda (x y) (tag (+ x y))))
  (put 'sub '(scheme-number scheme-number)
       (lambda (x y) (tag (- x y))))
  (put 'mul '(scheme-number scheme-number)
       (lambda (x y) (tag (* x y))))
  (put 'div '(scheme-number scheme-number)
       (lambda (x y) (tag (/ x y))))
  (put 'make 'scheme-number
       (lambda (x) (tag x)))
  ;problem 2.80
  (put '=zero? '(scheme-number)
    (lambda (a) (= a 0)))
  'done)

(install-scheme-number-package)

(define (make-scheme-number n)
  ((get 'make 'scheme-number) n))


;; ===================================================================
;; ======================== Rational package =========================
;; ===================================================================

(define (install-rational-package)
  ;; internal procedures
  (define (numer x) (car x))
  (define (denom x) (cdr x))
  (define (make-rat n d)
    (let ((g (gcd n d)))
      (cons (/ n g) (/ d g))))
  (define (add-rat x y)
    (make-rat (+ (* (numer x) (denom y))
                 (* (numer y) (denom x)))
              (* (denom x) (denom y))))
  (define (sub-rat x y)
    (make-rat (- (* (numer x) (denom y))
                 (* (numer y) (denom x)))
              (* (denom x) (denom y))))
  (define (mul-rat x y)
    (make-rat (* (numer x) (numer y))
              (* (denom x) (denom y))))
  (define (div-rat x y)
    (make-rat (* (numer x) (denom y))
              (* (denom x) (numer y))))

  ;; z1a/z1b = z2a/z2b  iff z1a*z2b - z2a*z1b = 0
  ;; equ? for problem 2.79
  (define (equ? z1 z2)
    (= (- (* (numer z1) (denom z2))
          (* (numer z2) (denom z1)))
        0))
  ;; interface to rest of the system
  (put 'equ? '(rational rational) equ?)
  (define (tag x) (attach-tag 'rational x))
  (put 'add '(rational rational)
       (lambda (x y) (tag (add-rat x y))))
  (put 'sub '(rational rational)
       (lambda (x y) (tag (sub-rat x y))))
  (put 'mul '(rational rational)
       (lambda (x y) (tag (mul-rat x y))))
  (put 'div '(rational rational)
       (lambda (x y) (tag (div-rat x y))))
  (put 'make 'rational
       (lambda (n d) (tag (make-rat n d))))
  ;problem 2.80
  (put '=zero? '(rational)
    (lambda (a) (= (numer a) 0)))
  'done)

(install-rational-package)

(define (make-rational n d)
  ((get 'make 'rational) n d))

;; ===================================================================
;; ================= Complex polar and rectangular ===================
;; ===================================================================

(define (install-polar-package)
  ;; internal procedures
  (define (magnitude z) (car z))
  (define (angle z) (cdr z))
  (define (make-from-mag-ang r a) (cons r a))
  (define (real-part z)
    (* (magnitude z) (cos (angle z))))
  (define (imag-part z)
    (* (magnitude z) (sin (angle z))))
  (define (make-from-real-imag x y)
    (cons (sqrt (+ (square x) (square y)))
          (atan y x)))
  ;; interface to the rest of the system
  (define (tag x) (attach-tag 'polar x))
  (put 'real-part '(polar) real-part)
  (put 'imag-part '(polar) imag-part)
  (put 'magnitude '(polar) magnitude)
  (put 'angle '(polar) angle)
  (put 'make-from-real-imag 'polar
       (lambda (x y) 
         (tag (make-from-real-imag x y))))
  (put 'make-from-mag-ang 'polar
       (lambda (r a) 
         (tag (make-from-mag-ang r a))))
  'done)
(install-polar-package)

(define (install-rectangular-package)
  ;; internal procedures
  (define (real-part z) (car z))
  (define (imag-part z) (cdr z))
  (define (make-from-real-imag x y)
    (cons x y))
  (define (magnitude z)
    (sqrt (+ (square (real-part z))
             (square (imag-part z)))))
  (define (angle z)
    (atan (imag-part z) (real-part z)))
  (define (make-from-mag-ang r a)
    (cons (* r (cos a)) (* r (sin a))))
  ;; interface to the rest of the system
  (define (tag x)
    (attach-tag 'rectangular x))
  (put 'real-part '(rectangular) real-part)
  (put 'imag-part '(rectangular) imag-part)
  (put 'magnitude '(rectangular) magnitude)
  (put 'angle '(rectangular) angle)
  (put 'make-from-real-imag 'rectangular
       (lambda (x y)
         (tag (make-from-real-imag x y))))
  (put 'make-from-mag-ang 'rectangular
       (lambda (r a)
         (tag (make-from-mag-ang r a))))
  'done)
(install-rectangular-package)

;; ===================================================================
;; ========================= Complex package =========================
;; ===================================================================

(define (install-complex-package)
  ;; imported procedures from rectangular 
  ;; and polar packages
  (define (real-part z)
    (apply-generic 'real-part z))
  (define (imag-part z)
    (apply-generic 'imag-part z))
  (define (magnitude z)
    (apply-generic 'magnitude z))
  (define (angle z)
    (apply-generic 'angle z))

  (define (make-from-real-imag x y)
    ((get 'make-from-real-imag 
          'rectangular) 
     x y))
  (define (make-from-mag-ang r a)
    ((get 'make-from-mag-ang 'polar) 
     r a))
  ;; internal procedures
  (define (add-complex z1 z2)
    (make-from-real-imag 
     (+ (real-part z1) (real-part z2))
     (+ (imag-part z1) (imag-part z2))))
  (define (sub-complex z1 z2)
    (make-from-real-imag 
     (- (real-part z1) (real-part z2))
     (- (imag-part z1) (imag-part z2))))
  (define (mul-complex z1 z2)
    (make-from-mag-ang 
     (* (magnitude z1) (magnitude z2))
     (+ (angle z1) (angle z2))))
  (define (div-complex z1 z2)
    (make-from-mag-ang 
     (/ (magnitude z1) (magnitude z2))
     (- (angle z1) (angle z2))))

  (define (equ? z1 z2) ; for problem 2.79
    (and (= (real-part z1) (real-part z2)) 
         (= (imag-part z1) (imag-part z2))))
  ;; interface to rest of the system
  (put 'equ? '(complex complex) equ?)
  (put 'real-part '(complex) real-part) ; Changes from problem 2.77
  (put 'imag-part '(complex) imag-part)
  (put 'magnitude '(complex) magnitude)
  (put 'angle '(complex) angle)

  (define (tag z) (attach-tag 'complex z))
  (put 'add '(complex complex)
       (lambda (z1 z2) 
         (tag (add-complex z1 z2))))
  (put 'sub '(complex complex)
       (lambda (z1 z2) 
         (tag (sub-complex z1 z2))))
  (put 'mul '(complex complex)
       (lambda (z1 z2) 
         (tag (mul-complex z1 z2))))
  (put 'div '(complex complex)
       (lambda (z1 z2) 
         (tag (div-complex z1 z2))))
  (put 'make-from-real-imag 'complex
       (lambda (x y) 
         (tag (make-from-real-imag x y))))
  (put 'make-from-mag-ang 'complex
       (lambda (r a) 
         (tag (make-from-mag-ang r a))))
  ;problem 2.80
  (put '=zero? '(complex)
    (lambda (z) (and (= (real-part z) 0) (= (imag-part z) 0))))
  'done)

(install-complex-package)

(define (=zero? a)
  (apply-generic '=zero? a))
(define (real-part z)
  (apply-generic 'real-part z))
(define (imag-part z)
  (apply-generic 'imag-part z))
(define (magnitude z)
  (apply-generic 'magnitude z))
(define (angle z)
  (apply-generic 'angle z))
(define (equ? a b)
  (apply-generic 'equ? a b))

(define (make-complex-from-real-imag x y)
  ((get 'make-from-real-imag 'complex) x y))
(define (make-complex-from-mag-ang r a)
  ((get 'make-from-mag-ang 'complex) r a))

;; Crazy test cases (test cases generated by gemini 2.5 pro)
 
;; ===================================================================
;; ===================== Coercion Procedures =======================
;; ===================================================================
(define (scheme-number->rational n) (make-rational (contents n) 1))
(define (scheme-number->complex n) (make-complex-from-real-imag (contents n) 0))
(define (rational->complex r)
  (let ((rat-val (contents r)))
    (make-complex-from-real-imag (/ (car rat-val) (cdr rat-val)) 0)))

;; Install the coercions
(put-coercion 'scheme-number 'rational scheme-number->rational)
(put-coercion 'scheme-number 'complex scheme-number->complex)
(put-coercion 'rational 'complex rational->complex)
(display "Coercions installed.") (newline)


;; ===================================================================
;; ======================== Test Variables =========================
;; ===================================================================
(define sn1 (make-scheme-number 5))
(define sn2 (make-scheme-number -2))
(define rat1 (make-rational 1 2))
(define rat2 (make-rational 3 4))
(define comp1 (make-complex-from-real-imag 2 3))
(define comp2 (make-complex-from-real-imag 1 1))


;; ===================================================================
;; ========================== Test Suite ===========================
;; ===================================================================
(newline) (display "--- Testing Basic Operations ---") (newline)
(display "Add SN+SN: ") (display (apply-generic 'add sn1 sn2)) (newline)
(display "Add Rat+Rat: ") (display (apply-generic 'add rat1 rat2)) (newline)
(display "Add Comp+Comp: ") (display (apply-generic 'add comp1 comp2)) (newline)

(newline) (display "--- Testing Simple Coercion (2 Args) ---") (newline)
(display "Add SN+Rat: ") (display (apply-generic 'add sn1 rat1)) (newline) ; Expect Rat (11 . 2)
(display "Add Rat+SN: ") (display (apply-generic 'add rat1 sn1)) (newline) ; Expect Rat (11 . 2)
(display "Add SN+Comp: ") (display (apply-generic 'add sn1 comp1)) (newline) ; Expect Comp (rect 7 . 3)
(display "Add Comp+SN: ") (display (apply-generic 'add comp1 sn1)) (newline) ; Expect Comp (rect 7 . 3)
(display "Add Rat+Comp: ") (display (apply-generic 'add rat1 comp2)) (newline) ; Expect Comp (rect 1.5 . 1)
(display "Add Comp+Rat: ") (display (apply-generic 'add comp2 rat1)) (newline) ; Expect Comp (rect 1.5 . 1)

(newline) (display "--- Testing Equ? with Coercion ---") (newline)
(display "Equ? SN=Rat: ") (display (equ? (make-scheme-number 3) (make-rational 6 2))) (newline) ; Expect #t
(display "Equ? Rat=Comp: ") (display (equ? (make-rational 3 2) (make-complex-from-real-imag 1.5 0))) (newline) ; Expect #t
(display "Equ? SN=Comp: ") (display (equ? sn1 (make-complex-from-real-imag 5 0))) (newline) ; Expect #t
(display "Equ? SN!=Comp: ") (display (equ? sn1 comp1)) (newline) ; Expect #f

