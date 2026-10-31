%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% CC-EC_TF-TC.cls, V1.1, 2026/06/26
% Developed by Marcelo Trindade Rebonatto
% Updated by Rafael Rieder
% Adapted from RBCA v3.0 class model, developed by Carlos Amaral Hölbig
% 
% V1.1
% - versão para trabalhos de conclusão e trabalhos finais de curso
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%

\ProvidesClass{CC-EC_TF-TC}[2025/07/24, v1.1]

\newif\if@numrefs
\newif\if@alpharefs

%% Options for bibliography style
\DeclareOption{num-refs}{
  \@numrefstrue
  \@alpharefsfalse
}
\DeclareOption{alpha-refs}{
  \@numrefsfalse
  \@alpharefstrue
}

\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}

%%\ExecuteOptions{num-refs}
\ProcessOptions\relax
\LoadClass[twoside,twocolumn]{article}

\RequirePackage[brazilian=nohyphenation,english=nohyphenation]{hyphsubst}
\RequirePackage{babel} 
%\RequirePackage[utf8]{inputenc}
\RequirePackage[T1]{fontenc}
\RequirePackage{microtype}
\RequirePackage{merriweather}
  \renewcommand{\ttdefault}{lmtt}
\RequirePackage[italic]{mathastext}
\RequirePackage{relsize}
\RequirePackage{ragged2e}
\RequirePackage{xcolor}
\RequirePackage{colortbl}
\RequirePackage{graphicx}
\RequirePackage{etoolbox,xpatch}
\RequirePackage{environ}
\RequirePackage{lastpage}
\RequirePackage{rotating}
\RequirePackage{lscape}
\RequirePackage{afterpage}
\RequirePackage[absolute]{textpos}
\RequirePackage{url}
\RequirePackage{xurl}
\RequirePackage{newfloat}
\RequirePackage{mdframed}
\RequirePackage{titlesec}
\RequirePackage{setspace}
\RequirePackage{threeparttable}
\RequirePackage{epstopdf}
\RequirePackage{siunitx}
\RequirePackage{amsmath}
\RequirePackage{xstring}

\RequirePackage{listings}
\lstset{
  numbers=left, 
  xleftmargin=2em,
  framexleftmargin=1.5em,
  frame=single,
  numbersep=5pt, 
  backgroundcolor=\color{gray!10},
  commentstyle=\scriptsize\color{blue},
  basicstyle=\scriptsize
} 

\RequirePackage{scrextend}
  \changefontsizes[10.5pt]{9pt}

\RequirePackage{calc}
\RequirePackage{geometry}
\geometry{
  letterpaper,
  includefoot,
  hmargin=4pc+6.64pt,
  bottom=2pc+6pt,
  top=6pc+6pt,
  headsep=2pc,
  headheight=17.5pt,
  footnotesep=1pc+6pt,
  columnsep=18pt
}
\setlength{\parindent}{12pt}

\RequirePackage[flushmargin,bottom]{footmisc}

\RequirePackage[colorlinks,bookmarksopen,bookmarksnumbered,citecolor=blue,urlcolor=blue, linkcolor=blue]{hyperref}

\RequirePackage[nameinlink,capitalize]{cleveref}

\RequirePackage[noblocks]{authblk}
  \newbox{\myorcidbox}
  \sbox{\myorcidbox}{}
  \newcommand{\orcid}[1]{%
	\href{https://orcid.org/#1}{\textsuperscript{\usebox{\myorcidbox},}}}

% \RequirePackage{translations}
%   \DeclareTranslation{English}{rec_paper}{Received: }
%   \DeclareTranslation{Brazilian}{rec_paper}{Recebido: }
%   \DeclareTranslation{English}{rev_paper}{Revised: }
%   \DeclareTranslation{Brazilian}{rev_paper}{Revisado: }
%   \DeclareTranslation{English}{acc_paper}{Accepted: }
%   \DeclareTranslation{Brazilian}{acc_paper}{Aceito: }

% Editora UPF logo file
%\def\@upflogo{editora_logo.png}
\def\@upflogo{logoColorHorizontalComplemento.png}

% RBCA logo file
\def\@jlogo{rbca_logo.png}%

% RBCA full name
\def\@jname{Trabalho de Conclusão de Curso}%

% Paper settings: page numbers
\newcommand{\firstpage}[1]{\def\@firstpage{#1}}
\def\@jpages{\@firstpage--\pageref*{LastPage}}   % paper page numbers
\newcommand{\jpages}[1]{\def\@jpages{#1}}
\definecolor{jcolour}{RGB}{0,100,0}          % paper basic color

% Paper settings: year, volume, issue, month, DOI and paper ID
\newcommand{\jyear}[1]{\def\@jyear{#1}}
\newcommand{\jvolume}[1]{\def\@jvolume{#1}}
\newcommand{\jissue}[1]{\def\@jissue{#1}}
\newcommand{\jmonth}[1]{\def\@jmonth{#1}}
\newcommand{\jid}[1]{\def\@jid{#1}}
\newcommand{\jcourse}[1]{\def\@jcourse{#1}}


% Paper settings: paper dates
\newcommand{\jrec}[1]{\def\@jrec{#1}}
\newcommand{\jrev}[1]{\def\@jrev{#1}}
\newcommand{\jacc}[1]{\def\@jacc{#1}}


% Paper settings: titles, abstract/resumo and authors
\newcommand{\runningauthor}[1]{\def\@runningauthor{#1}}
\newcommand{\runningtitle}[1]{\def\@runningtitle{#1}}
\newcommand{\corraddress}[1]{\def\@corraddress{#1}}
\newcommand{\authnote}[1]{\appto{\@authnotes}{#1\par}}
\newcommand{\papercat}[1]{\def\@papercat{#1}}
\newcommand{\titleother}[1]{\def\@titleother{#1}}
\newcommand{\titulores}[1]{\def\@titulores{#1}}




\RequirePackage{fancyhdr}
\fancyhf{}
\renewcommand{\headrule}{\color{jcolour}\rule{\textwidth}{2pt}}

\chead{
	\fontsize{9pt}{10pt}\selectfont%
	\color{jcolour}%
	\@runningauthor \hspace{1em}\raisebox{-0.5pt}{|}\hspace{1em}%
	% \textit{\@jname}~(\@jyear), v.\@jvolume, n.\@jissue, pp.\@jpages%
    \textit{\@titulores}~(\@jmonth / \@jyear)%
}

\fancyhead[RO,LE]{
	\fontsize{9pt}{10pt}\selectfont%
	\color{jcolour}% 
	\thepage%
}

\pagestyle{fancy}


\AtBeginDocument{%
  \newsavebox{\@gscitedetails}
  \newlength{\@gscitedetailsheight}
  \newsavebox{\@gsheadbox}
  \newlength{\@gsheadboxheight}
  
  \savebox{\@gscitedetails}{%
    \parbox{\textwidth-21pc+4pc+6.64pt}{%
    {\color{jcolour}\rule{\linewidth-2cm}{2pt}}\par%
    \vspace{\dimexpr 10pt-1em\relax}%
    \fontsize{8pt}{9.5pt}\bfseries%
    Curso de ~\@jcourse \par
    % Vol.~\@jvolume, N$^{\underline{o}}$~\@jissue, pp.~\@jpages \par
    Passo Fundo, ~\@jmonth, ~\@jyear \par
    \ifnum\pdfstrcmp{\@jcourse}{Ciência da Computação}=0
        Homepage: \href{https://repositorio.upf.br/handle/123456789/8754}{https://repositorio.upf.br/handle/123456789/8754}\par
    \else
        \ifnum\pdfstrcmp{\@jcourse}{Engenharia de Computação}=0
            Homepage: \href{https://repositorio.upf.br/handle/123456789/8757}{https://repositorio.upf.br/handle/123456789/8757}\par
        \else
            Homepage: \href{https://repositorio.upf.br}{https://repositorio.upf.br}\par
        \fi
    \fi
    Páginas: ~\@jpages \par
    \vspace{\dimexpr 8pt-1em\relax}%
    {\color{jcolour}\rule{\linewidth-2cm}{2pt}}\par
  }}%
  \settototalheight{\@gscitedetailsheight}{\usebox{\@gscitedetails}}%
  %%%%
  \savebox{\@gsheadbox}{%
    \parbox{\textwidth-21pc+4pc+6.64pt}{%
    \normalfont%
    \fontsize{7.5pt}{9.5pt}\selectfont%
    % {\bfseries\@jname, \@jmonth, \@jyear}\par
    \vspace{\dimexpr 4pt-1.5pt\relax}%
    \usebox{\@gscitedetails}
    }%
  }%
  \settototalheight{\@gsheadboxheight}{\usebox{\@gsheadbox}}%
}

\RequirePackage{alphalph}
\newalphalph{\fnsymbolmult}[mult]{\@fnsymbol}{5}

\newcounter{authorfn}
\setcounter{authorfn}{1}
\newcommand{\authfn}[1]{%
  \fnsymbolmult{#1}%
}

\renewcommand\Authand{ e }
\renewcommand\Authands{, }
\renewcommand\AB@affilsepx{, }
\renewcommand{\Authfont}{\fontsize{13pt}{18pt}\selectfont}
\renewcommand{\Affilfont}{\fontsize{9pt}{13pt}\selectfont}
\setlength{\affilsep}{21pt-9pt}

\AtBeginDocument{
\renewcommand{\@maketitle}{%
  \textblockorigin{4pc+6.64pt}{4pc+6pt}
  %%%%
  \begin{textblock*}{21pc}(0pt,0pt)
  \IfFileExists{\@upflogo}{%
    % \includegraphics[height=\@gsheadboxheight]{\@upflogo}%
    \includegraphics[scale=0.15]{\@upflogo}%
  }{%
    \fbox{\begin{minipage}[b][\@gsheadboxheight]{\@gsheadboxheight}
    \raggedright
    Placeholder for UPF Editora logo \@upflogo
    \end{minipage}}%
  }
  \hspace{22pt}%
  %% Do absolutely nothing if \@jlogo is empty string
  % \ifdefempty{\@jlogo}{}{%
  % \IfFileExists{\@jlogo}{%
  %   \includegraphics[height=\@gsheadboxheight]{\@jlogo}
  % }{%
  %   \fbox{\begin{minipage}[b][\@gsheadboxheight]{\@gsheadboxheight}%
  %   \raggedright Placeholder for RBCA logo \@jlogo
  %   \end{minipage}}%
  % }}
  \end{textblock*}
  %%%
  \begin{textblock*}{\textwidth-21pc}(21pc,0pt)
  \usebox{\@gsheadbox}
  \end{textblock*}%
  %%%
  \null\vspace*{\dimexpr 4pc\relax}%13pc+11pt-5pc-6pt
  \raggedright%
  {\fontsize{10pt}{16pt}\selectfont%
    \ifpdf
      \textls[200]{\textbf{\MakeUppercase{\@papercat}}}
    \else %%% don't use letterspace in latex+dvi
      \textbf{\MakeUppercase{\@papercat}}%
    \fi%
    \par}
  \vspace{\dimexpr 8pt\relax}
  
  % paper title
  \IfStrEq*{\languagename}{english}{
  {
   \centering
   \fontsize{16pt}{27pt}
   \bfseries
   \color{jcolour}
   \@title
   \par
  }
  }
  
  \IfStrEq*{\languagename}{brazilian}{
  {
   \centering
   \fontsize{16pt}{27pt}
   \bfseries
   \color{jcolour}
   \@title
   \par
  }
  \vspace{\dimexpr 13pt\relax}
  {
   \centering
   \fontsize{16pt}{27pt}
   \bfseries
   \color{jcolour}
   \@titleother
   \par
  }
  }
 
  \vspace{\dimexpr 13pt\relax}
  
  % paper authors
  \centering{\@author}\par
  \vspace{\dimexpr 15.5pt-1em}
  {%
    \renewcommand{\authfn}[1]{%
    \textsuperscript{\fnsymbolmult{##1}}%
    }
    % {\fontsize{8pt}{9.5pt}\selectfont\@authnotes\par}%
    %   \vspace{\dimexpr 15.5pt-1em}
    %   \textbf{\GetTranslation{rec_paper}}\@jrec.
    %   \textbf{\GetTranslation{rev_paper}}\@jrev.
    %   \textbf{\GetTranslation{acc_paper}}\@jacc.\par%
    {\noindent\color{jcolour}\rule{\hsize}{3pt}}\par%
  }
  \vspace{\dimexpr 13pt-1em\relax}
}
}

\RequirePackage[style]{abstract}
\setlength{\absleftindent}{0pt}
\setlength{\absrightindent}{0pt}
\setlength{\absparindent}{12pt}
\setlength{\absparsep}{0pt}
\setlength{\abstitleskip}{8pt-\baselineskip}
\renewcommand{\abstractnamefont}{\fontsize{11pt}{12pt}\bfseries\color{jcolour}}
\renewcommand{\abstitlestyle}[1]{{\abstractnamefont #1}}
\renewcommand{\abstracttextfont}{\fontsize{9pt}{11pt}\selectfont}

\preto{\abstract}{%
  \vspace*{\dimexpr 13pt\relax}
}
\appto\abstract{\noindent\ignorespaces}
\preto\endabstract{\par}

\newenvironment{Abstract}{
	\def\abstractname{Abstract}
	\begin{abstract}
	}{
	\end{abstract}
}

\newenvironment{keywords}
{\vspace*{\dimexpr 11pt-\baselineskip\relax}%
\noindent\fontsize{9pt}{11pt}\selectfont\textbf{Keywords}: \ignorespaces}%
{\par}{\par}


\newenvironment{resumo}{
	\def\abstractname{Resumo}
	\begin{abstract}
	}{
	\end{abstract}
}


\newenvironment{palavras_chave}
{\vspace*{\dimexpr 11pt-\baselineskip\relax}%
	\noindent\fontsize{9pt}{11pt}\selectfont\textbf{Palavras-Chave}: \ignorespaces}%
{\par}

\if@twocolumn
  \NewEnviron{frontmatter}
  {\twocolumn[%
      \BODY%
      \vspace*{\dimexpr 16pt-3pt-1em\relax}
      {\noindent\color{jcolour}\rule{\hsize}{3pt}}\par
      \vspace*{\dimexpr 23pt-1em\relax}]%
  }
\else
  \NewEnviron{frontmatter}{%
      \BODY%
      \vspace*{\dimexpr 16pt-3pt-1em\relax}
      {\noindent\color{jcolour}\rule{\hsize+4pc+6.64pt}{3pt}}\par
      \vspace*{\dimexpr 23pt-1em\relax}%
  }
\fi

\setcounter{secnumdepth}{4}
\titleformat*{\section}{\fontsize{11pt}{12pt}\bfseries\color{jcolour}}
\titlespacing*{\section}{0pt}{26.5pt-1em}{16pt-1em}

\titleformat*{\subsection}{\fontsize{10pt}{11pt}\bfseries\color{jcolour}}
\titlespacing*{\subsection}{0pt}{2pc-1em}{17pt-1em}

\titleformat*{\subsubsection}{\fontsize{9pt}{11pt}\bfseries\slshape\color{jcolour}}
\titlespacing*{\subsubsection}{0pt}{\baselineskip}{0pt}

\titleformat{\paragraph}[runin]{\color{jcolour}\fontsize{9pt}{11pt}\itshape}{\theparagraph}{5pt}{}[.\enspace]
\titlespacing*{\paragraph}{0pt}{\baselineskip}{0pt}

\RequirePackage{enumitem}
\setlist{noitemsep}
\setlist[itemize]{leftmargin=12pt,topsep=16pt-1em}
\setlist[enumerate]
{itemindent=14pt,topsep=16.8pt-1em,
 label={\roman*.},labelsep=7pt,
 labelwidth=*,leftmargin=*,align=right}


% quotes and epigraphs
\RequirePackage{quoting}
\newcommand{\quotefont}{\fontsize{6.5pt}{9.5pt}\selectfont}
\quotingsetup{vskip=16pt-1em,indentfirst=false,font={quotefont},leftmargin=12pt,rightmargin=12pt}

\renewenvironment{quote}{\begin{quoting}}{\end{quoting}}

\renewenvironment{quotation}{\begin{quoting}}{\end{quoting}}

\newenvironment{epigraph}[1]
{\begin{quoting}[font={itshape,fontsize{7.5pt}{10.5pt}},vskip=15pt-1em,leftmargin=0pt,rightmargin=0pt]%
 \def\@quotesource{#1}}
{\par\vspace{\dimexpr 15pt-1em\relax}{\upshape---\@quotesource}\end{quoting}}

% Space above/below equations
\g@addto@macro\normalsize{%
  \setlength\abovedisplayskip{\baselineskip}%
  \setlength\belowdisplayskip{\baselineskip}%
  \setlength\abovedisplayshortskip{\baselineskip}%
  \setlength\belowdisplayshortskip{\baselineskip}%
}

\RequirePackage{stfloats}
\RequirePackage{booktabs}
\RequirePackage{tabularx}
% Left-, right- and center-aligned auto-wrapping column types
\newcolumntype{L}{>{\raggedright\arraybackslash}X}
\newcolumntype{R}{>{\raggedleft\arraybackslash}X}
\newcolumntype{C}{>{\centering\arraybackslash}X}

\AtBeginEnvironment{tabularx}{%
  \fontsize{8pt}{10pt}\selectfont
}
\AtBeginEnvironment{tabular}{%
  \fontsize{8pt}{10pt}\selectfont
}

\setlength{\aboverulesep}{11pt-1em}
\setlength{\belowrulesep}{11pt-1em}
\setlength{\heavyrulewidth}{0.5pt}
\setlength{\lightrulewidth}{0.5pt}
\arrayrulecolor{jcolour}


\RequirePackage[tableposition=top]{caption}
\DeclareCaptionFont{figcaptionfont}{\fontsize{9pt}{9pt}\selectfont}
\DeclareCaptionFont{tabcaptionfont}{\fontsize{9pt}{9pt}\selectfont}
\captionsetup{justification=centering,singlelinecheck=false,labelfont={bf},labelsep=colon}
\captionsetup*[figure]{font=figcaptionfont,skip=10pt}
\captionsetup*[table]{font=tabcaptionfont,skip=10pt-1em}

% Skips for floats
\setlength{\floatsep}{1pc+6pt}
\setlength{\intextsep}{1pc+6pt}
\setlength{\textfloatsep}{1pc+6pt}

% References
\if@numrefs
  \RequirePackage[numbers]{natbib }
  \bibliographystyle{agsm}
\fi
\if@alpharefs
    \RequirePackage[semicolon]{natbib}
    \bibliographystyle{dcu}
\fi