# Asymptotic approximations and some notes on $\Theta$, $\Omega$, $O$. 

SICP covers the notation $\Theta(f(n)),$ but for a function $g(n)$ to be order $\Theta(f(n))$ is a 
pretty restrictive thing. In fact there's a whole asymptotic toolkit that's useful for 
math, computer science, and physics, and it's kind of a shame that it's not taught sooner! Actually
if you get nothing else out of this article, it's that you should go watch Carl Bender's lecture series
on asymptotics. 

<iframe width="560" height="315" src="https://www.youtube.com/embed/LYNOGk3ZjFM?si=ulaELbRC-a_tg0VM" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

He gives the whole lecture series while trying to hide a smile because some of the formulas
he writes on the board are pretty good jokes, like the diverging factorial sum we'll encounter in this article!
I wanted to give some preview of these tools and tell you why I love them, as well as show you how they're
useful on at least one SICP practice problem.

## Useful definitions

To start out, assuming you've read section 1.2 in SICP, you know the definition of $\Theta(f(n)).$ To 
write it more succinctly using quantifiers "there exists" ($\exists$) and "for all" ($\forall$):

**Definition.** For positive functions $f(n)$ and $R(n)$, we write that $R(n)$ is $\Theta(f(n))$ as $n\to\infty$ if:
$$\exists_{c_1,c_2,N}:\forall_{n\gt N}\;\; 0 \leq c_1 f(n) \leq R(n)\leq c_2 f(n)$$

That's fine and all, but a more typical approach is found in *The Algorithm Design Manual* by Skiena. We first define $O(n)$ and $\Omega(n),$ and define $\Theta(n)$ in terms of them.

**Definition.** We write that $R(n)$ is $O(f(n))$ as $n\to \infty$ if
$$\exists_{c,N}:\forall_{n\gt N}\;\; R(n)\leq c \cdot f(n)$$
$R(n)=O(f(n))$ is a statement that the growth rate of $R(n)$ is bounded above by $f(n)$ times a constant, for sufficiently large $n.$
 
**Definition.** We write that $R(n)$ is $\Omega(f(n))$ as $n\to\infty$ if
$$\exists_{c,N}:\forall_{n\gt N}\;\; 0 \leq c \cdot f(n) \leq R(n)$$
$R(n)=\Omega(f(n))$ is a statement that the growth rate of $R(n)$ is bounded below by $f(n)$ times a constant, for sufficiently large $n.$

These two statements can also be written $R(n)=O(f(n))$ and $R(n)=\Omega(f(n)).$ With those two definitions, we then say that $R(n)=\Theta(f(n))$ if $R(n)=\Omega(f(n))$ and $R(n)=O(f(n)).$ 

This is great, and now there's another super useful notation. This is introduced in *Concrete Mathematics* by Graham, Knuth, and Patashnik as $f(n)\succ g(n),$ but I know it with the notation used in Skiena, $f(n)\gg g(n).$ This is read out loud as "$f(n)$ dominates $g(n)$." The symbol used in Concrete Mathematics is $\succ$ or `\succ`, so I suppose you could also read this as 
"$f(n)$ succeeds $g(n)$" as a mnemonic for the LaTeX, if you prefer that symbol. Anyways, its definition...

**Definition.** We write $f(n)\gg g(n)$ as $n\to a$ if $\lim_{n\to a} \frac{g(n)}{f(n)}=0.$ This definition gives:
$$n!\gg 2^n \gg n^3\gg n^2\gg n\log n\gg n\gg \log n \gg 1$$

Finally, the most useful tool of all is $\sim,$ which is used when the ratio of two functions doesn't approach zero or infinity, but approaches $1$ instead. "$\sim$" is read as "is asymptotic to."

**Definition.** $f(n)\sim g(n)$ as $n\to a$ if $\lim_{n\to a} \frac{g(n)}{f(n)}=1.$

Before we get too far afield, let's use this to solve a problem from SICP.

## Using asymptotics to solve recurrence relations.

I found that for exercise **1.14** we end up really wishing we had a bigger asymptotics toolbelt!

For my solution of the exercise, I dealt with a function $T(a,n)$ representing the 
number of nodes needed to evaluate the relevant function. We end up with a series of recurrence relations:

<div>$$\begin{align*}
T(a,1)&=T(a-1,1)+2\\
T(a,2)&=T(a,1)+T(a-5,2)+1\\
T(a,3)&=T(a,2)+T(a-10,3)+1\\
T(a,4)&=T(a,3)+T(a-25,4)+1\\
T(a,5)&=T(a,4)+T(a-50,5)+1
\end{align*}$$</div>

There are some base cases which we could analyze by hand: $T(0,1)$ is just some constant, $T(0,2)$, $T(1,2)$, $T(2,2)$ are just constants and so on. The big question is: What is the big Theta growth order of $T(a,5)$? 

I'll admit my recurrence relation solving skills are awful, but $T(a,1)$ is easy. We just apply the relation
a bunch until we get to zero:

$$T(a,1)=2a+T(0,1)$$

Next, the recurrence for $T(a,2).$ This is a little bit tougher... with some elbow grease 
(or using Wolfram Alpha or mathematica's [RSolve](https://reference.wolfram.com/language/ref/RSolve.html)) we find that

<div>$$T(a,2)=\frac{a^2+(6+T(0,1))a}{5}+C(a\textrm{ mod }5,2),$$</div>

where $C$ is some constant term that takes into account that we get the base cases right. 
But the big takeaway here is that $T(a,2)=\Theta(a^2).$ 

With our larger asymptotics toolkit, we can also see that $$T(a,2)\sim a^2/5.$$ 

With a discerning eye, we can also think to write $$T(a,2)-\frac{a^2}{5}\sim \frac{6+T(0,1)}{5} a.$$

Basically, asymptotics allows us to find $T$ in increasing levels of granularity! The order of growth is
the easiest. Getting the leading factor is a tiny bit harder, and getting the subleading factor takes yet more work. 

If we were to solve for $T(a,3)$ exactly, we'd get another complicated polynomial and more constants, 
but we should know by now to only look at the dominant terms. We find $T(a,3)=\Theta(a^3),$ and the 
asymptotics of the leading term can be expressed as
$$T(a,3)\sim \frac{1}{150} a^3.$$

The point is that asymptotics gives us the tools to talk about this all formally, and then 
it becomes clear that we don't have to solve the problem in anything but the least level of granularity. 
$T(a,4)=\Theta(a^4),$ $T(a,5)=\Theta(a^5),$ and there we go, we've solved the problem.

*Side note:* Interestingly, in my book club we ran into a problem where we tried to work out the asymptotics of $T$ by evaluating the code and timing it, then looking at the slope on a log-log plot. 
But we didn't go to a high enough $a$ to get a clear result! A detailed asymptotic analysis
would have shown that the $a^5$ term only becomes dominant around $a\approx 300.$

## An aside on asymptotic series and Stirling's approximation

The topic of Stirling's approximation also came up in our book club's meeting. 
That's a good thing because the asymptotics we've learned so far allows us to point out a little quirk that 
usually isn't emphasized. Stirling's approximation can be written as:

$$\log(n!)=n\log(n)-n+\frac{1}{2}\log(2\pi n) + \sum_{k=2}^M \frac{(-1)^k B_k}{k(k-1)n^{k-1}} + O\left(\frac{1}{n^M}\right)$$

On first glance we might think that this looks like a Taylor series or a Laurent series, but we'd be mistaken! 
There are two awkward aspects:
1. In a Taylor series we have good reason to choose monomials $x^k$ as our basis functions
and we're guaranteed that a Taylor series of an analytic function is unique. 
But how do we justify expanding $\log(n!)$ in terms of $n\log(n)$? Once we start expanding with weird terms, 
do we still have uniqueness?
2. If we look at the coefficients $B_k,$ these are the Bernoulli numbers. We find that they grow very quickly.
They grow so quickly in fact, that if we tried to take
$M\to\infty$ the sum wouldn't converge for any finite $n.$ What gives?!

The resolution of these questions arises from defining an *asymptotic series* as follows. Note that writing the upper limit of the sum as infinity is an abuse of notation---*we never actually carry out the infinite sum*.

**Definition.** We write $g(n)\sim \sum_{i=1}^\infty f_i(n)$ as $n\to a$ if:

 - $f_1(n)\sim g(n)$ as $n\to a$
 - The remainder is asymptotic to $f_2$. That is, $$f_2(n)\sim g(n)-f_1(n)\textrm{ as }n\to a.$$
 - That remainder is asymptotic to $f_3$. That is, $$f_3(n)\sim g(n)-f_1(n)-f_2(n)\textrm{ as }n\to a.$$ 

With these definitions, we can get a whole theory of asymptotic series along with uniqueness guarantees, such as those in 
Bender and Orszag's *Advanced Mathematical Methods for Scientists and Engineers*. This is the sense in which
the Stirling approximation is an asymptotic series for $n!.$

## Another application of asymptotic series

Stirling's approximation is too fancy for my blood, the presence of the Bernoulli numbers detracts 
from the essence of what's going on and there's a simpler example that we can grasp completely. 

Say that you're stuck on a desert island with only sand and the integral

$$f(a)=\int_0^\infty \frac{e^{-x/a}}{1+x} \mathrm{d}x.$$

You have to compute $f(0.1),$ how do you do it?
Well, let's use a series expansion and repeated integration by parts. 
We'll totally ignore issues of convergence and real analysis. 
<div>$$\begin{align*}
\int_0^\infty \frac{e^{-x/a}}{1+x} \mathrm{d}x &= \int_0^\infty e^{-x/a}\sum_{n=0}^\infty (-1)^n x^n \mathrm{d}x \\
&= \sum_{n=0}^\infty \int_0^\infty (-1)^n e^{-x/a} x^n \mathrm{d}x \\
&= \sum_{n=0}^\infty (-1)^n n!a^{n+1} \tag{integrate by parts}\\
\end{align*}$$</div>
This infinite sum has a radius of convergence of zero! However if we plug in $a=0.1$ and keep the first few terms, we get
$$f(0.1)\approx 0.1 - 0.01 + 0.002 - 0.0006 + 0.00024=0.09164$$
compare this to the true value of $f(0.1)=0.0915633\ldots,$ it's a pretty good approximation! How weird is that,
by truncating a divergent series we got a good result. In the exact same way, by truncating the Stirling expansion, we get good results. 

Really what we've shown is that as an asymptotic series,
$$\int_0^\infty \frac{e^{-a x}}{1+x} \mathrm{d}x \sim \sum_{n=0}^\infty (-1)^n n!a^{n+1} \tag{as $a\to 0$}$$

Another interesting tidbit: We can't expect any Taylor expansion to exist around $a=0,$ because the integral diverges for $a<0.$

I learned this from Bender and Orszag's "Advanced Mathematical Methods for Scientists and Engineers: Asymptotic Methods and Perturbation Theory". The title is a mouthful, and it comes across a lot better in video format. Carl Bender writes a lot of these equations with a smile on his face, because $\sum_{n-1}^\infty (-1)^n n!$ is an absurd sum and is kind of a joke! To a physicist or applied mathematician, what we mean by the infinite sum is really $f(1)$ where $f$ is the perfectly well-defined transcendental function given as an integral above.

<iframe width="560" height="315" src="https://www.youtube.com/embed/LYNOGk3ZjFM?si=ulaELbRC-a_tg0VM" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## Other Resources and Summary

Okay, so followup books are:

 - *The Algorithm Design Manual* by Skiena
 - *Concrete Mathematics* by Graham, Knuth, and Patashnik

And then into the stuff that's more for the combinatorics and theoretical physicist peeps:

 - *Generatingfunctionology* by Wilf
 - *Advanced Mathematical Methods for Scientists and Engineers* by Bender and Orszag
 - *Analytic Combinatorics* by Sedgewick and Flajolet

I know a lot of this stuff from statistical mechanics, statistical field theory, and quantum field theory. So you can imagine the reference list and topic list could explode to infinite length here. Important integrals are...

- The formula that forms the basics of Feynman diagrams, which are terms in an asymptotic series. The fast growth rate of these
coefficients means that the series doesn't typically converge, and so we're dealing with asymptotics.
$$\int_{-\infty}^\infty x^{2n}e^{-x^2/2}/\sqrt{2\pi} \mathrm{d}x = (2n-1)!!$$ 

- The [Sommerfeld expansion](https://en.wikipedia.org/wiki/Sommerfeld_expansion) of Fermi-Dirac statistics (for example, the electrons in a metal at room temperature are well-described by a degenerate Fermi-Dirac gas). Note that for large $\beta$ (=low temperature), the function $\frac{1}{e^{\beta x}+1}$ looks like a step function. So we get the answer for the step function, plus a correction term when $\beta$ is less-than-infinite. A step function isn't very analytic, and so this also explains why we have an asymptotic series instead of a convergent power series.
<div>$${\displaystyle \int _{-\infty }^{\infty }{\frac {H(\varepsilon )}{e^{\beta (\varepsilon -\mu )}+1}}\,\mathrm {d} \varepsilon =\int _{-\infty }^{\mu }H(\varepsilon )\,\mathrm {d} \varepsilon +{\frac {\pi ^{2}}{6}}\left({\frac {1}{\beta }}\right)^{2}H^{\prime }(\mu )+O\left({\frac {1}{\beta \mu }}\right)^{4}}$$</div>
