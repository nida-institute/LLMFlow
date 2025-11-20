<xsl:stylesheet version="3.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:tei="http://www.crosswire.org/2013/TEIOSIS/namespace"
  xmlns:local="http://local.functions"
  xmlns:map="http://www.w3.org/2005/xpath-functions/map"
  xmlns:xs="http://www.w3.org/2001/XMLSchema"
  xmlns="http://www.crosswire.org/2013/TEIOSIS/namespace"
  exclude-result-prefixes="tei local map xs">

  <xsl:output method="xml" indent="yes" encoding="UTF-8"/>
  <xsl:global-context-item use="required" as="node()"/>

  <xsl:param name="use-body-choice-abbreviations" as="xs:boolean" select="false()"/>
  <xsl:param name="use-conjectural-expansions" as="xs:boolean" select="false()"/>

  <xsl:variable name="abbreviation-catalog" as="map(xs:string, map(xs:string, xs:string))">
    <xsl:map>
      <xsl:map-entry key="'general'">
        <xsl:map>
          <xsl:map-entry key="'absol.'" select="'absolute'"/>
          <xsl:map-entry key="'acc.'" select="'accusative'"/>
          <xsl:map-entry key="'act.'" select="'active'"/>
          <xsl:map-entry key="'ad fin.'" select="'to the end'"/>
          <xsl:map-entry key="'adj.'" select="'adjective'"/>
          <xsl:map-entry key="'adv.'" select="'adverb'"/>
          <xsl:map-entry key="'al.'" select="'elsewhere'"/>
          <xsl:map-entry key="'alibi'" select="'elsewhere'"/>
          <xsl:map-entry key="'aor.'" select="'aorist'"/>
          <xsl:map-entry key="'Apocr.'" select="'Apocrypha'"/>
          <xsl:map-entry key="'App.'" select="'Appendix'"/>
          <xsl:map-entry key="'Aram.'" select="'Aramaic'"/>
          <xsl:map-entry key="'art.'" select="'article'"/>
          <xsl:map-entry key="'Att.'" select="'Attic'"/>
          <xsl:map-entry key="'bibl.'" select="'biblical'"/>
          <xsl:map-entry key="'bis'" select="'twice'"/>
          <xsl:map-entry key="'c.'" select="'with'"/>
          <xsl:map-entry key="'cum.'" select="'with'"/>
          <xsl:map-entry key="'cf.'" select="'compare'"/>
          <xsl:map-entry key="'cl.'" select="'PICKONE classics, classical'"/>
          <xsl:map-entry key="'cogn.'" select="'cognate'"/>
          <xsl:map-entry key="'compar.'" select="'comparative'"/>
          <xsl:map-entry key="'contr.'" select="'contracted'"/>
          <xsl:map-entry key="'dat.'" select="'dative'"/>
          <xsl:map-entry key="'def.'" select="'definite'"/>
          <xsl:map-entry key="'demonstr.'" select="'demonstrative'"/>
          <xsl:map-entry key="'e.g.'" select="'for instance'"/>
          <xsl:map-entry key="'eccl.'" select="'ecclesiastical'"/>
          <xsl:map-entry key="'esp.'" select="'especially'"/>
          <xsl:map-entry key="'ex.'" select="'example'"/>
          <xsl:map-entry key="'exc.'" select="'except'"/>
          <xsl:map-entry key="'f.'" select="'and following (verse)'"/>
          <xsl:map-entry key="'ff.'" select="'and following (verses)'"/>
          <xsl:map-entry key="'fig.'" select="'figurative'"/>
          <xsl:map-entry key="'freq.'" select="'frequent'"/>
          <xsl:map-entry key="'fut.'" select="'future'"/>
          <xsl:map-entry key="'gen.'" select="'genitive'"/>
          <xsl:map-entry key="'gloss.'" select="'glossary'"/>
          <xsl:map-entry key="'Heb.'" select="'Hebrew'"/>
          <xsl:map-entry key="'i.e.'" select="'that is'"/>
          <xsl:map-entry key="'ib.'" select="'in the same place'"/>
          <xsl:map-entry key="'id.'" select="'the same'"/>
          <xsl:map-entry key="'impers.'" select="'impersonal'"/>
          <xsl:map-entry key="'impf.'" select="'imperfect'"/>
          <xsl:map-entry key="'impv.'" select="'imperative'"/>
          <xsl:map-entry key="'in l.'" select="'in that place'"/>
          <xsl:map-entry key="'indic.'" select="'indicative'"/>
          <xsl:map-entry key="'inf.'" select="'infinitive'"/>
          <xsl:map-entry key="'infr.'" select="'infra'"/>
          <xsl:map-entry key="'Ion.'" select="'Ionic'"/>
          <xsl:map-entry key="'l.c.'" select="'in the place cited'"/>
          <xsl:map-entry key="'m.'" select="'masculine'"/>
          <xsl:map-entry key="'metaph.'" select="'metaphorically'"/>
          <xsl:map-entry key="'meton.'" select="'metonymy'"/>
          <xsl:map-entry key="'MGr.'" select="'Modern Greek'"/>
          <xsl:map-entry key="'n.'" select="'PICKONE: note, neuter'"/>
          <xsl:map-entry key="'neg.'" select="'negative'"/>
          <xsl:map-entry key="'nom.'" select="'nominative'"/>
          <xsl:map-entry key="'pl.'" select="'plural'"/>
          <xsl:map-entry key="'poss.'" select="'possessive'"/>
          <xsl:map-entry key="'pron.'" select="'pronoun'"/>
          <xsl:map-entry key="'sg.'" select="'singular'"/>
          <xsl:map-entry key="'om.'" select="'PICKONE: omit, omits'"/>
          <xsl:map-entry key="'opp.'" select="'opposed to'"/>
          <xsl:map-entry key="'optat.'" select="'optative'"/>
          <xsl:map-entry key="'pass.'" select="'passive'"/>
          <xsl:map-entry key="'pers.'" select="'person'"/>
          <xsl:map-entry key="'pf.'" select="'perfect'"/>
          <xsl:map-entry key="'plpf.'" select="'pluperfect'"/>
          <xsl:map-entry key="'prep.'" select="'preposition'"/>
          <xsl:map-entry key="'prop.'" select="'properly'"/>
          <xsl:map-entry key="'ptcp.'" select="'participle'"/>
          <xsl:map-entry key="'q.v.'" select="'see that entry'"/>
          <xsl:map-entry key="'rei'" select="'of the thing'"/>
          <xsl:map-entry key="'s.'" select="'sub'"/>
          <xsl:map-entry key="'s.v.'" select="'see the entry for'"/>
          <xsl:map-entry key="'se.'" select="'that is'"/>
          <xsl:map-entry key="'seq.'" select="'followed by'"/>
          <xsl:map-entry key="'subjc.'" select="'subjunctive'"/>
          <xsl:map-entry key="'subst.'" select="'substantive'"/>
          <xsl:map-entry key="'superl.'" select="'superlative'"/>
          <xsl:map-entry key="'supr.'" select="'earlier in this entry'"/>
          <xsl:map-entry key="'syn.'" select="'synonym'"/>
          <xsl:map-entry key="'Targ.'" select="'Targum'"/>
          <xsl:map-entry key="'V.'" select="'see'"/>
          <xsl:map-entry key="'vb.'" select="'verb'"/>
          <xsl:map-entry key="'v.l.'" select="'variant reading'"/>
          <xsl:map-entry key="'v.s.'" select="'see under'"/>
          <xsl:map-entry key="'w.'" select="'with'"/>
        </xsl:map>
      </xsl:map-entry>
      <xsl:map-entry key="'biblical.septuagint'">
        <xsl:map>
          <xsl:map-entry key="'Ge'" select="'Genesis'"/>
          <xsl:map-entry key="'Ex'" select="'Exodus'"/>
          <xsl:map-entry key="'Le'" select="'Leviticus'"/>
          <xsl:map-entry key="'Nu'" select="'Numbers'"/>
          <xsl:map-entry key="'De'" select="'Deuteronomy'"/>
          <xsl:map-entry key="'Jos'" select="'Joshua'"/>
          <xsl:map-entry key="'Jg'" select="'Judges'"/>
          <xsl:map-entry key="'Ru'" select="'Ruth'"/>
          <xsl:map-entry key="'I, II Ki'" select="'I, II Kings (E.V., Samuel)'"/>
          <xsl:map-entry key="'III, IV Ki'" select="'III, IV Kings (E.V., I, II Kings)'"/>
          <xsl:map-entry key="'I, II Ch'" select="'I, II Chronicles'"/>
          <xsl:map-entry key="'II Es'" select="'II Esdras (E.V., Ezra)'"/>
          <xsl:map-entry key="'Ne'" select="'Nehemiah'"/>
          <xsl:map-entry key="'Es'" select="'Esther'"/>
          <xsl:map-entry key="'Jb'" select="'Job'"/>
          <xsl:map-entry key="'Ps'" select="'Psalms'"/>
          <xsl:map-entry key="'Pr'" select="'Proverbs'"/>
          <xsl:map-entry key="'Ec'" select="'Ecclesiastes'"/>
          <xsl:map-entry key="'Ca'" select="'Canticles'"/>
          <xsl:map-entry key="'Is'" select="'Isaiah'"/>
          <xsl:map-entry key="'Je'" select="'Jeremiah'"/>
          <xsl:map-entry key="'La'" select="'Lamentations'"/>
          <xsl:map-entry key="'Ez'" select="'Ezekiel'"/>
          <xsl:map-entry key="'Da'" select="'Daniel'"/>
          <xsl:map-entry key="'Ho'" select="'Hosea'"/>
          <xsl:map-entry key="'Jl'" select="'Joel'"/>
          <xsl:map-entry key="'Am'" select="'Amos'"/>
          <xsl:map-entry key="'Ob'" select="'Obadiah'"/>
          <xsl:map-entry key="'Jh'" select="'Jonah'"/>
          <xsl:map-entry key="'Mi'" select="'Micah'"/>
          <xsl:map-entry key="'Na'" select="'Nahum'"/>
          <xsl:map-entry key="'Hb'" select="'Habakkuk'"/>
          <xsl:map-entry key="'Ze'" select="'Zephaniah'"/>
          <xsl:map-entry key="'Hg'" select="'Haggai'"/>
          <xsl:map-entry key="'Za'" select="'Zachariah'"/>
          <xsl:map-entry key="'Ma'" select="'Malachi'"/>
          <xsl:map-entry key="'I Es'" select="'I Esdras'"/>
          <xsl:map-entry key="'To'" select="'Tobit'"/>
          <xsl:map-entry key="'Jth'" select="'Judith'"/>
          <xsl:map-entry key="'Wi'" select="'Wisdom'"/>
          <xsl:map-entry key="'Si'" select="'Sirach'"/>
          <xsl:map-entry key="'Ba'" select="'Baruch'"/>
          <xsl:map-entry key="'Da Su'" select="'Susannah'"/>
          <xsl:map-entry key="'Da Bel'" select="'Bel and the Dragon'"/>
          <xsl:map-entry key="'Pr Ma'" select="'Prayer of Manasseh'"/>
          <xsl:map-entry key="'I-IV Mac'" select="'I-IV Maccabees'"/>
        </xsl:map>
      </xsl:map-entry>
      <xsl:map-entry key="'biblical.new-testament'">
        <xsl:map>
          <xsl:map-entry key="'Mt'" select="'Matthew'"/>
          <xsl:map-entry key="'Mk'" select="'Mark'"/>
          <xsl:map-entry key="'Lk'" select="'Luke'"/>
          <xsl:map-entry key="'Jo'" select="'John'"/>
          <xsl:map-entry key="'Ac'" select="'Acts'"/>
          <xsl:map-entry key="'Ro'" select="'Romans'"/>
          <xsl:map-entry key="'I, II Co'" select="'I, II Corinthians'"/>
          <xsl:map-entry key="'Ga'" select="'Galatians'"/>
          <xsl:map-entry key="'Eph'" select="'Ephesians'"/>
          <xsl:map-entry key="'Phl'" select="'Philippians'"/>
          <xsl:map-entry key="'Col'" select="'Colossians'"/>
          <xsl:map-entry key="'I, II Th'" select="'I, II Thessalonians'"/>
          <xsl:map-entry key="'I, II Ti'" select="'I, II Timothy'"/>
          <xsl:map-entry key="'Tit'" select="'Titus'"/>
          <xsl:map-entry key="'Phm'" select="'Philemon'"/>
          <xsl:map-entry key="'He'" select="'Hebrews'"/>
          <xsl:map-entry key="'Ja'" select="'James'"/>
          <xsl:map-entry key="'I, II Pe'" select="'I, II Peter'"/>
          <xsl:map-entry key="'I-III Jo'" select="'I-III John'"/>
          <xsl:map-entry key="'Ju'" select="'Jude'"/>
          <xsl:map-entry key="'Re'" select="'Revelation'"/>
        </xsl:map>
      </xsl:map-entry>
      <xsl:map-entry key="'biblical.versions'">
        <xsl:map>
          <xsl:map-entry key="'Al.'" select="'anon, version quoted by Origen'"/>
          <xsl:map-entry key="'Aq.'" select="'Aquila'"/>
          <xsl:map-entry key="'AV'" select="'Authorized Version'"/>
          <xsl:map-entry key="'B'" select="'Beza'"/>
          <xsl:map-entry key="'E'" select="'Elzevir'"/>
          <xsl:map-entry key="'EV'" select="'English Version (A.V. and R.V.)'"/>
          <xsl:map-entry key="'Gr. Ven.'" select="'Graecus Venetus'"/>
          <xsl:map-entry key="'L'" select="'Lachmann'"/>
          <xsl:map-entry key="'LXX'" select="'Septuagint'"/>
          <xsl:map-entry key="'R (in LXX refs.)'" select="'Sixtine Edition of the Septuagint (1587)'"/>
          <xsl:map-entry key="'Rec.'" select="'Received Text'"/>
          <xsl:map-entry key="'RV'" select="'Revised Version'"/>
          <xsl:map-entry key="'R, txt., mg.'" select="'R.V. text, margin'"/>
          <xsl:map-entry key="'Sm.'" select="'Symmachus'"/>
          <xsl:map-entry key="'T'" select="'Tischendorf'"/>
          <xsl:map-entry key="'Th.'" select="'Theodotion'"/>
          <xsl:map-entry key="'Tr.'" select="'Tregelles'"/>
          <xsl:map-entry key="'Vg.'" select="'Vulgate'"/>
          <xsl:map-entry key="'WH'" select="'Westcott and Hort'"/>
        </xsl:map>
      </xsl:map-entry>
      <xsl:map-entry key="'ancient.witnesses'">
        <xsl:map>
          <xsl:map-entry key="'Ael.'" select="'Aelian'"/>
          <xsl:map-entry key="'Æsch.'" select="'Æschylus'"/>
          <xsl:map-entry key="'Æschin.'" select="'Æschines'"/>
          <xsl:map-entry key="'Anth.'" select="'Anthology'"/>
          <xsl:map-entry key="'Antonin.'" select="'M. Aurel. Antoninus'"/>
          <xsl:map-entry key="'Apoll. Rhod.'" select="'Apollonius Rhodius'"/>
          <xsl:map-entry key="'Arist.'" select="'Aristotle'"/>
          <xsl:map-entry key="'Aristoph.'" select="'Aristophanes'"/>
          <xsl:map-entry key="'Ath.'" select="'Athanasius'"/>
          <xsl:map-entry key="'CIG'" select="'Corpus Inscriptionum Graecarum'"/>
          <xsl:map-entry key="'Dio Cass.'" select="'Dio Cassius'"/>
          <xsl:map-entry key="'Diod.'" select="'Diodorus Siculus'"/>
          <xsl:map-entry key="'Diog. Laert.'" select="'Diogenes Laertius'"/>
          <xsl:map-entry key="'Dion. H.'" select="'Dionysius of Halicarnassus'"/>
          <xsl:map-entry key="'Diosc.'" select="'Dioscorides'"/>
          <xsl:map-entry key="'Eur.'" select="'Euripides'"/>
          <xsl:map-entry key="'Eustath.'" select="'Eustathius'"/>
          <xsl:map-entry key="'FlJ'" select="'Flavius Josephus'"/>
          <xsl:map-entry key="'Greg. Naz.'" select="'Gregory of Nazianzus'"/>
          <xsl:map-entry key="'Hdt.'" select="'Herodotus'"/>
          <xsl:map-entry key="'Heliod.'" select="'Heliodorus'"/>
          <xsl:map-entry key="'Herm.'" select="'Hermas'"/>
          <xsl:map-entry key="'Hes.'" select="'Hesiod'"/>
          <xsl:map-entry key="'Hipp.'" select="'Hippocrates'"/>
          <xsl:map-entry key="'Hom.'" select="'Homer'"/>
          <xsl:map-entry key="'Inscr.'" select="'Inscriptions'"/>
          <xsl:map-entry key="'Luc.'" select="'Lucian'"/>
          <xsl:map-entry key="'Lys.'" select="'Lysias'"/>
          <xsl:map-entry key="'Menand.'" select="'Menander'"/>
          <xsl:map-entry key="'π.'" select="'Papyri'"/>
          <xsl:map-entry key="'Paus.'" select="'Pausanias'"/>
          <xsl:map-entry key="'Phalar.'" select="'Phalaris'"/>
          <xsl:map-entry key="'Philo.'" select="'Philo Judaeus'"/>
          <xsl:map-entry key="'Pind.'" select="'Pindar'"/>
          <xsl:map-entry key="'Plat.'" select="'Plato'"/>
          <xsl:map-entry key="'Plut.'" select="'Plutarch'"/>
          <xsl:map-entry key="'Polyb.'" select="'Polybius'"/>
          <xsl:map-entry key="'Socr., HE'" select="'Socrates (Historia Ecclesiastica)'"/>
          <xsl:map-entry key="'Soph.'" select="'Sophocles'"/>
          <xsl:map-entry key="'Strab.'" select="'Strabo'"/>
          <xsl:map-entry key="'Test. Zeb.'" select="'Testimony of Zebedee'"/>
          <xsl:map-entry key="'Theogn.'" select="'Theognis'"/>
          <xsl:map-entry key="'Theophr.'" select="'Theophrastus'"/>
          <xsl:map-entry key="'Thuc.'" select="'Thucydides'"/>
          <xsl:map-entry key="'Xen.'" select="'Xenophon'"/>
        </xsl:map>
      </xsl:map-entry>
      <xsl:map-entry key="'modern.witnesses'">
        <xsl:map>
          <xsl:map-entry key="'Abbott, Essays'" select="'Essays chiefly on the Original Texts of the Old and New Testaments, by T. K. Abbott. Longmans, 1891'"/>
          <xsl:map-entry key="'Abbott, JG'" select="'Johannine Grammar, by E. A. Abbott. London, 1906'"/>
          <xsl:map-entry key="'Abbott, JV'" select="'Johannine Vocabulary, by the same. London, 1905'"/>
          <xsl:map-entry key="'AR'" select="'St. Paul''s Epistle to the Ephesians, by J. Armitage Robinson. Second Edition. Macmillan, 1909'"/>
          <xsl:map-entry key="'BDB'" select="'A Hebrew and English Lexicon of the Old Testament, by Brown, Driver, and Briggs. Oxford, 1906'"/>
          <xsl:map-entry key="'Blass, Gosp.'" select="'Philology of the Gospels, by F. Blass. Macmillan, 1898'"/>
          <xsl:map-entry key="'Blass, Gr.'" select="'Grammar of N.T. Greek, by F. Blass, translated by H. St. J. Thackeray. Macmillan, 1898'"/>
          <xsl:map-entry key="'Boisacq'" select="'Dictionnaire Etymologique de la langue Grecque, par Emile Boisacq. Paris, 1907-1914'"/>
          <xsl:map-entry key="'Burton'" select="'New Testament Moods and Tenses, by E. de W. Burton. Third Edition. University of Chicago, 1898'"/>
          <xsl:map-entry key="'CGT'" select="'Cambridge Greek Testament for Schools and Colleges'"/>
          <xsl:map-entry key="'Charles, APOT'" select="'Apocrypha and Pseudepigrapha of the Old Testament, by R. H. Charles. Oxford, 1913'"/>
          <xsl:map-entry key="'CR'" select="'Classical Review. London, 1887 ff.'"/>
          <xsl:map-entry key="'Cremer'" select="'Biblico-Theological Lexicon of N.T. Greek, by H. Cremer. Third English Edition, with Supplement. T. &amp; T. Clark, 1886'"/>
          <xsl:map-entry key="'Dalman, Gt.'" select="'Grammatik des jüdisch-palästinensischen Aramäisch, by G. Dalman. Leipzig, 1894'"/>
          <xsl:map-entry key="'Dalman, Words'" select="'The Words of Jesus, by G. Dalman. English Edition. T. &amp; T. Clark, 1902'"/>
          <xsl:map-entry key="'DAC'" select="'Dictionary of the Apostolic Church, edited by J. Hastings. Volume I. Scribners, 1915'"/>
          <xsl:map-entry key="'DB'" select="'Dictionary of the Bible, edited by J. Hastings. Five volumes (i-iv, extra volume). Scribners, 1898-1904'"/>
          <xsl:map-entry key="'DB 1-vol.'" select="'Dictionary of the Bible (one volume), by J. Hastings. Scribners, 1909'"/>
          <xsl:map-entry key="'DCG'" select="'Dictionary of Christ and the Gospels, edited by J. Hastings. Two volumes. Scribners, 1907-08'"/>
          <xsl:map-entry key="'Deiss., BS'" select="'Bible Studies, by G. A. Deissmann. Second English Edition, translated by A. Grieve. T. &amp; T. Clark, 1909'"/>
          <xsl:map-entry key="'Deiss., LAE'" select="'Light from the Ancient East, by A. Deissmann, translated by L. R. M. Strachan. Second Edition. Hodder, 1908'"/>
          <xsl:map-entry key="'EB'" select="'Encyclopaedia Biblica. Four volumes. London, 1899-1903'"/>
          <xsl:map-entry key="'Edwards, Lex.'" select="'An English-Greek Lexicon, by G. M. Edwards. Cambridge, 1912'"/>
          <xsl:map-entry key="'EGT'" select="'Expositor''s Greek Testament'"/>
          <xsl:map-entry key="'Ellic.'" select="'Commentary on St. Paul''s Epistles, by C. J. Ellicott. Andover, 1860-65'"/>
          <xsl:map-entry key="'Enc. Brit.'" select="'Encyclopaedia Britannica. Eleventh Edition. Cambridge University Press, 1910'"/>
          <xsl:map-entry key="'Exp. Times'" select="'The Expository Times, edited by J. Hastings. T. &amp; T. Clark, 1890 ff.'"/>
          <xsl:map-entry key="'Field, Notes'" select="'Notes on the Translation of the N.T., by F. Field. Cambridge, 1899'"/>
          <xsl:map-entry key="'Gifford, Inc.'" select="'The Incarnation, by E. Gifford. Hodder, 1897'"/>
          <xsl:map-entry key="'Grimm-Thayer'" select="'A Greek-English Lexicon of the N.T., being Grimm''s Wilke''s Clavis Novi Testamenti, translated by J. H. Thayer. New York, 1897'"/>
          <xsl:map-entry key="'Hatch, Essays'" select="'Essays in Biblical Greek, by Edwin Hatch. Oxford, 1889'"/>
          <xsl:map-entry key="'Hort'" select="'Commentaries on the Greek Text of the Epistle of St. James (1:1-4:7); The First Epistle of St. Peter (1:1-2:17); and the Apocalypse of St. John (1-3), by F. J. A. Hort. Macmillan, 1898-1909'"/>
          <xsl:map-entry key="'ICC'" select="'International Critical Commentary. Scribners'"/>
          <xsl:map-entry key="'Interp. Comm.'" select="'Interpreter''s Commentary. New York, Barnes &amp; Co.'"/>
          <xsl:map-entry key="'Jannaris'" select="'A Historical Greek Grammar, by A. N. Jannaris. Macmillan, 1897'"/>
          <xsl:map-entry key="'JThS'" select="'Journal of Theological Studies. London, 1899 ff.'"/>
          <xsl:map-entry key="'Kennedy, Sources'" select="'Sources of N.T. Greek, by H. A. A. Kennedy. T. &amp; T. Clark, 1895'"/>
          <xsl:map-entry key="'Kühner³'" select="'Ausführliche Grammatik der griechischen Sprache, by R. Kühner. Third Edition, by F. Blass and B. Gerth. Four volumes, 1890-1904'"/>
          <xsl:map-entry key="'Lft.'" select="'Commentaries on St. Paul''s Epistles to the Galatians (1892); Philippians (Third Edition, 1873); and Colossians and Philemon (1892), by J. B. Lightfoot. Macmillan. Also Apostolic Fathers, five volumes. Macmillan, 1890'"/>
          <xsl:map-entry key="'Lft., Notes'" select="'Notes on Epistles of St. Paul, by J. B. Lightfoot. Macmillan, 1895'"/>
          <xsl:map-entry key="'LS'" select="'A Greek-English Lexicon, by H. G. Liddell and R. Scott. Seventh Edition. Harper, 1889'"/>
          <xsl:map-entry key="'Mayor'" select="'Commentaries on the Epistle of St. James (Third Edition, 1910), and the Epistle of St. Jude and the Second Epistle of St. Peter. Macmillan, 1907'"/>
          <xsl:map-entry key="'Mayser'" select="'Grammatik der griechischen Papyri aus der Ptolemäerzeit, by E. Mayser. Leipzig, 1906'"/>
          <xsl:map-entry key="'M''Neile'" select="'The Gospel according to St. Matthew, by A. H. M''Neile. Macmillan, 1915'"/>
          <xsl:map-entry key="'Meyer'" select="'Critical and Exegetical Commentary on the N.T., by H. A. W. Meyer. English translation, T. &amp; T. Clark, 1883'"/>
          <xsl:map-entry key="'Milligan, Selections'" select="'Selections from the Greek Papyri, by G. Milligan. Cambridge, 1910'"/>
          <xsl:map-entry key="'MM (xi-xxv)'" select="'Lexical Notes from the Papyri, by J. H. Moulton and G. Milligan. Expositor VII, vi, 567 ff.; VIII, iv, 561 ff.'"/>
          <xsl:map-entry key="'MM (s.v.)'" select="'The Vocabulary of the Greek Testament, by J. H. Moulton and G. Milligan. Part I (α); Part II (β-δ). Hodder, 1914-15'"/>
          <xsl:map-entry key="'M, Pr.'" select="'A Grammar of N.T. Greek. Volume I, Prolegomena, by J. H. Moulton. Third Edition. Scribners, 1908'"/>
          <xsl:map-entry key="'M, Th.'" select="'St. Paul''s Epistles to the Thessalonians, by G. Milligan. Macmillan, 1908'"/>
          <xsl:map-entry key="'Moffatt'" select="'James Moffatt, An Introduction to the Literature of the N.T. Scribners, 1911'"/>
          <xsl:map-entry key="'Mozley, Ps.'" select="'The Psalter of the Church, by P. W. Mozley. Cambridge, 1905'"/>
          <xsl:map-entry key="'NTD'" select="'The New Testament Documents, by G. Milligan. Macmillan, 1913'"/>
          <xsl:map-entry key="'Page'" select="'The Acts of the Apostles, by T. E. Page. Macmillan, 1903'"/>
          <xsl:map-entry key="'Rackham'" select="'The Acts of the Apostles, by R. B. Rackham. Methuen, 1901'"/>
          <xsl:map-entry key="'Ramsay, St. Paul'" select="'St. Paul the Traveller and the Roman Citizen, by W. M. Ramsay. Hodder, 1895'"/>
          <xsl:map-entry key="'Rendall'" select="'The Epistle to the Hebrews, by F. Rendall. Macmillan, 1911'"/>
          <xsl:map-entry key="'Rutherford, NPhr.'" select="'The New Phrynichus, by W. G. Rutherford. Macmillan, 1881'"/>
          <xsl:map-entry key="'Schmidt'" select="'J. H. Heinrich Schmidt, Synonymik der Griechischen Sprache. Four volumes. Leipzig, 1876-1886'"/>
          <xsl:map-entry key="'Simcox'" select="'W. H. Simcox, The Language of the New Testament. Second Edition. Hodder, 1892'"/>
          <xsl:map-entry key="'Soph., Lex.'" select="'Greek Lexicon of the Roman and Byzantine Periods, by E. A. Sophocles. Scribners, 1900'"/>
          <xsl:map-entry key="'Swete'" select="'Commentaries on the Gospel according to St. Mark (Third Edition, 1909) and the Apocalypse of St. John, by H. B. Swete. Macmillan, 1906'"/>
          <xsl:map-entry key="'Thackeray, Gr.'" select="'A Grammar of the O.T. in Greek I, by H. St. J. Thackeray. Cambridge, 1909'"/>
          <xsl:map-entry key="'Thayer'" select="'Grimm-Thayer, see there'"/>
          <xsl:map-entry key="'Thumb, Handh.'" select="'Handbook of the Modern Greek Vernacular, by A. Thumb. Translated from the Second German Edition by S. Angus. T. &amp; T. Clark, 1912'"/>
          <xsl:map-entry key="'Thumb, Hellen.'" select="'Die Griechische Sprache im Zeitalter des Hellenismus, by A. Thumb. Strassburg, 1901'"/>
          <xsl:map-entry key="'Tdf., Pr.'" select="'Novum Testamentum Graece, C. Tischendorf. Editio octava critica maior. Volume III, Prolegomena, by C. R. Gregory. Leipzig, 1894'"/>
          <xsl:map-entry key="'Tr., Syn.'" select="'Synonyms of the N.T., by R. C. Trench. Ninth Edition. Macmillan, 1880'"/>
          <xsl:map-entry key="'Vau.'" select="'St. Paul''s Epistle to the Romans, by C. F. Vaughan. Sixth Edition. Macmillan, 1885'"/>
          <xsl:map-entry key="'Veitch'" select="'Greek Verbs, Irregular and Defective, by W. Veitch. Oxford, 1887'"/>
          <xsl:map-entry key="'Viteau'" select="'Étude sur le grec du N.T., by J. Viteau. Volume I, Le Verbe: Syntaxe des Propositions, 1893; Volume II, Sujet: Complément et Attribut, 1896'"/>
          <xsl:map-entry key="'VD, MGr.'" select="'E. Vincent and T. G. Dickson, A Handbook to Modern Greek. Second Edition. Macmillan, 1904'"/>
          <xsl:map-entry key="'Westc.'" select="'Commentaries on the Gospel according to St. John, by B. F. Westcott, two volumes, Murray, 1908; the Epistle to the Ephesians, Macmillan, 1906; the Epistles of St. John, Third Edition. Macmillan, 1892'"/>
          <xsl:map-entry key="'WH'" select="'The N.T. in the original Greek, by B. F. Westcott and F. J. A. Hort. Volume II, Introduction and Appendix. Macmillan, 1881'"/>
          <xsl:map-entry key="'WM'" select="'A Grammar of N.T. Greek, translated from G. B. Winer''s seventh edition, with large additions, by W. P. Moulton. Third Edition. T. &amp; T. Clark, 1882'"/>
          <xsl:map-entry key="'WS'" select="'Grammatik des neutestamentlichen Sprachidioms, von G. B. Winer. Eighth edition revised by P. W. Schmiedel. Göttingen, 1894'"/>
          <xsl:map-entry key="'Zorell'" select="'Novi Testamenti Lexicon Graecum (Cursus Scripturae Sacrae I, vii), auctore Fr. Zorell, S.J. Paris, 1911'"/>
        </xsl:map>
      </xsl:map-entry>
    </xsl:map>
  </xsl:variable>

  <xsl:variable name="conjectural-books" as="xs:string*"
    select="('I','II','III','IV','V','VI','VII','VIII','IX','X')"/>

  <xsl:variable name="book-abbreviations" as="xs:string*"
    select="distinct-values((
      map:keys(map:get($abbreviation-catalog, 'biblical.septuagint')),
      map:keys(map:get($abbreviation-catalog, 'biblical.new-testament'))
    ))"/>

  <xsl:variable name="book-abbreviations-letter-only" as="xs:string*"
    select="$book-abbreviations[matches(., '^[A-Za-z]+$')]"/>

  <xsl:variable name="abbr-tokens" as="xs:string*">
    <xsl:for-each select="map:keys($abbr-map)">
      <xsl:sort select="string-length(.)" data-type="number" order="descending"/>
      <xsl:sequence select="."/>
    </xsl:for-each>
  </xsl:variable>

  <xsl:function name="local:regex-escape" as="xs:string">
    <xsl:param name="value" as="xs:string"/>
    <xsl:sequence select="replace($value, '([\\.\^\$\|\?\*\+\(\)\{\}\[\]])', '\\\$1')"/>
  </xsl:function>

  <xsl:function name="local:is-book-abbreviation" as="xs:boolean">
    <xsl:param name="token" as="xs:string"/>
    <xsl:sequence select="some $b in $book-abbreviations-letter-only satisfies $token = $b"/>
  </xsl:function>

  <xsl:function name="local:expand-abbr" as="xs:string">
    <xsl:param name="text" as="xs:string"/>
    <xsl:iterate select="$abbr-tokens">
      <xsl:param name="current" select="$text"/>
      <xsl:on-completion select="$current"/>
      <xsl:variable name="token" select="."/>
      <xsl:variable name="has-dot-variant"
        select="not(ends-with($token, '.')) and map:contains($abbr-map, concat($token, '.'))"/>
      <xsl:variable name="pattern" as="xs:string">
        <xsl:choose>
          <xsl:when test="local:is-book-abbreviation($token)">
            <xsl:sequence
              select="concat('(^|\P{L})(', local:regex-escape($token),
                             ')((?:\s+(?:\d+|[IVXLCDMivxlcdm]+))|[:.;,)\]])')"/>
          </xsl:when>
          <xsl:when test="$has-dot-variant">
            <xsl:sequence
              select="concat('(^|\P{L})(', local:regex-escape($token), ')(\.)?(\P{L}|$)')"/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:sequence
              select="concat('(^|\P{L})(', local:regex-escape($token), ')(\P{L}|$)')"/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:variable>
      <xsl:variable name="replacement" select="map:get($abbr-map, $token)"/>
      <xsl:variable name="next" as="xs:string">
        <xsl:choose>
          <xsl:when test="string-length($token) = 0">
            <xsl:sequence select="$current"/>
          </xsl:when>
          <xsl:when test="local:is-book-abbreviation($token)">
            <xsl:sequence select="replace($current, $pattern, concat('$1', $replacement, '$3'))"/>
          </xsl:when>
          <xsl:when test="$has-dot-variant">
            <xsl:sequence select="replace($current, $pattern, concat('$1', $replacement, '$4'))"/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:sequence select="replace($current, $pattern, concat('$1', $replacement, '$3'))"/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:variable>
      <xsl:next-iteration>
        <xsl:with-param name="current" select="$next"/>
      </xsl:next-iteration>
    </xsl:iterate>
  </xsl:function>

  <xsl:template match="@* | node()" priority="-5">
    <xsl:copy copy-namespaces="no">
      <xsl:apply-templates select="@* | node()"/>
    </xsl:copy>
  </xsl:template>

  <xsl:template match="text()">
    <xsl:value-of select="local:expand-abbr(.)"/>
  </xsl:template>

  <xsl:template match="text()" mode="copy-clean">
    <xsl:value-of select="local:expand-abbr(.)"/>
  </xsl:template>

  <xsl:variable name="base-abbr-map" as="map(xs:string, xs:string)"
  select="local:catalog-to-map($abbreviation-catalog)"/>

<xsl:variable name="body-abbr-map" as="map(xs:string, xs:string)"
  select="if ($use-body-choice-abbreviations) then local:compute-body-choice-map(.) else map{}"/>

<xsl:variable name="abbr-map" as="map(xs:string, xs:string)"
  select="map:merge(($base-abbr-map, $body-abbr-map), map{'duplicates':'use-first'})"/>

  <xsl:function name="local:catalog-to-map" as="map(xs:string, xs:string)">
    <xsl:param name="catalog" as="map(xs:string, map(xs:string, xs:string))"/>
    <xsl:variable name="entries" as="map(xs:string, xs:string)*">
      <xsl:for-each select="map:keys($catalog)">
        <xsl:sequence select="local:map-with-dotless(map:get($catalog, .))"/>
      </xsl:for-each>
    </xsl:variable>
    <xsl:sequence select="if (exists($entries)) then map:merge($entries, map{'duplicates':'use-first'}) else map{}"/>
  </xsl:function>

  <xsl:function name="local:map-with-dotless" as="map(xs:string, xs:string)">
    <xsl:param name="source" as="map(xs:string, xs:string)"/>
    <xsl:variable name="entries" as="map(xs:string, xs:string)*">
      <xsl:for-each select="map:keys($source)">
        <xsl:variable name="abbr" select="."/>
        <xsl:variable name="expansion" select="map:get($source, $abbr)"/>
        <xsl:sequence select="map:entry($abbr, $expansion)"/>
        <xsl:if test="ends-with($abbr, '.')">
          <xsl:sequence select="map:entry(substring($abbr, 1, string-length($abbr) - 1), $expansion)"/>
        </xsl:if>
      </xsl:for-each>
    </xsl:variable>
    <xsl:sequence select="if (exists($entries)) then map:merge($entries, map{'duplicates':'use-first'}) else map{}"/>
  </xsl:function>

  <xsl:function name="local:compute-body-choice-map" as="map(xs:string, xs:string)">
    <xsl:param name="root" as="node()"/>
    <xsl:variable name="entries" as="map(xs:string, xs:string)*">
      <xsl:for-each select="$root//tei:choice[tei:abbr and (tei:expan or tei:note[@type=('expan','expansion')])]">
        <xsl:variable name="abbr" select="normalize-space(string-join(tei:abbr//text(), ' '))"/>
        <xsl:variable name="expansion-source" select="(tei:expan, tei:note[@type=('expan','expansion')])[1]"/>
        <xsl:variable name="expansion" select="normalize-space(string-join($expansion-source//text(), ' '))"/>
        <xsl:if test="$abbr and $expansion">
          <xsl:sequence select="map:entry($abbr, $expansion)"/>
          <xsl:if test="ends-with($abbr, '.')">
            <xsl:sequence select="map:entry(substring($abbr, 1, string-length($abbr) - 1), $expansion)"/>
          </xsl:if>
        </xsl:if>
      </xsl:for-each>
    </xsl:variable>
    <xsl:sequence select="if (exists($entries)) then map:merge($entries, map{'duplicates':'use-first'}) else map{}"/>
  </xsl:function>

</xsl:stylesheet>
