"""
Contenu du cahier de douâas et hadiths du Prophète ﷺ.

Textes authentiques issus des recueils canoniques (Bukhârî, Muslim, Abû
Dâwûd, Tirmidhî) — chaque entrée cite sa source. Ce module est chargé par
la commande de gestion `python manage.py seed_library` (idempotent : les
entrées existantes sont mises à jour par leur source).

Références standard utilisées pour les numéros :
  * Sahîh al-Bukhârî (édition classique)
  * Sahîh Muslim (édition standard)
  * Sunan Abû Dâwûd
  * Jâmi' at-Tirmidhî
"""

DUAS = [
    # ------------------------------------------------------------------
    # Réveil & sommeil
    # ------------------------------------------------------------------
    dict(
        category="reveil",
        title="Douâa au réveil",
        text_ar="الْحَمْدُ لِلَّهِ الَّذِي أَحْيَانَا بَعْدَ مَا أَمَاتَنَا وَإِلَيْهِ النُّشُورُ",
        transliteration="Al-hamdu lillâhi lladhî ahyânâ ba'da mâ amâtanâ wa ilayhi n-nushûr.",
        translation_fr="Louange à Allah qui nous a redonné la vie après nous l'avoir retirée, et c'est vers Lui qu'est la résurrection.",
        source="Sahîh al-Bukhârî 6312",
        order=1,
    ),
    dict(
        category="reveil",
        title="Douâa avant de dormir",
        text_ar="بِاسْمِكَ اللَّهُمَّ أَمُوتُ وَأَحْيَا",
        transliteration="Bismika llâhumma amûtu wa ahyâ.",
        translation_fr="En Ton nom, ô Allah, je meurs et je vis.",
        source="Sahîh al-Bukhârî 6324",
        order=2,
    ),
    dict(
        category="reveil",
        title="Protection du matin et du soir",
        text_ar="بِسْمِ اللَّهِ الَّذِي لَا يَضُرُّ مَعَ اسْمِهِ شَيْءٌ فِي الْأَرْضِ وَلَا فِي السَّمَاءِ وَهُوَ السَّمِيعُ الْعَلِيمُ",
        transliteration="Bismi llâhi lladhî lâ yadurru ma'a ismihi shay'un fî l-ardi wa lâ fî s-samâ'i wa huwa s-samî'u l-'alîm.",
        translation_fr="Au nom d'Allah, avec le nom duquel rien ne peut nuire sur terre ni au ciel, et Il est l'Audient, l'Omniscient.",
        source="Sunan Abû Dâwûd 5088 ; Jâmi' at-Tirmidhî 3388",
        order=3,
    ),
    dict(
        category="reveil",
        title="Douâa contre l'angoisse",
        text_ar="اللَّهُمَّ إِنِّي أَعُوذُ بِكَ مِنَ الْهَمِّ وَالْحَزَنِ وَالْعَجْزِ وَالْكَسَلِ وَالْبُخْلِ وَالْجُبْنِ وَضَلَعِ الدَّيْنِ وَغَلَبَةِ الرِّجَالِ",
        transliteration="Allâhumma innî a'ûdhu bika mina l-hammi wa l-hazani wa l-'ajzi wa l-kasali wa l-bukhli wa l-jubni wa dal'i d-dayni wa ghalabati r-rijâl.",
        translation_fr="Ô Allah, je cherche refuge auprès de Toi contre l'angoisse, la tristesse, l'impuissance, la paresse, l'avarice, la lâcheté, le poids de la dette et l'oppression des hommes.",
        source="Sahîh al-Bukhârî 6369",
        order=4,
    ),
    # ------------------------------------------------------------------
    # Repas
    # ------------------------------------------------------------------
    dict(
        category="repas",
        title="Douâa avant de manger",
        text_ar="بِسْمِ اللَّهِ",
        transliteration="Bismi llâh.",
        translation_fr="Au nom d'Allah. (Si l'on a oublié au début : « Bismi llâhi fî awwalihi wa âkhirihi » — au nom d'Allah au début et à la fin.)",
        source="Sahîh al-Bukhârî 5376",
        order=1,
    ),
    dict(
        category="repas",
        title="Douâa après avoir mangé",
        text_ar="الْحَمْدُ لِلَّهِ الَّذِي أَطْعَمَنِي هَذَا وَرَزَقَنِيهِ مِنْ غَيْرِ حَوْلٍ مِنِّي وَلَا قُوَّةٍ",
        transliteration="Al-hamdu lillâhi lladhî at'amanî hâdhâ wa razaqanîhi min ghayri hawlin minnî wa lâ quwwa.",
        translation_fr="Louange à Allah qui m'a nourri de ceci et me l'a accordé, sans aucune force ni puissance de ma part.",
        source="Sunan Abû Dâwûd 3850 ; Jâmi' at-Tirmidhî 3458",
        order=2,
    ),
    dict(
        category="repas",
        title="Douâa du jeûneur à la rupture",
        text_ar="ذَهَبَ الظَّمَأُ وَابْتَلَّتِ الْعُرُوقُ وَثَبَتَ الْأَجْرُ إِنْ شَاءَ اللَّهُ",
        transliteration="Dhahaba z-zama'u wa btallati l-'urûqu wa thabata l-ajru in shâ'a llâh.",
        translation_fr="La soif s'est éteinte, les veines sont désaltérées, et la récompense est acquise, si Allah le veut.",
        source="Sunan Abû Dâwûd 2357",
        order=3,
    ),
    # ------------------------------------------------------------------
    # Maison
    # ------------------------------------------------------------------
    dict(
        category="maison",
        title="Douâa en entrant chez soi",
        text_ar="بِسْمِ اللَّهِ وَلَجْنَا وَبِسْمِ اللَّهِ خَرَجْنَا وَعَلَى رَبِّنَا تَوَكَّلْنَا",
        transliteration="Bismi llâhi walajnâ wa bismi llâhi kharajnâ wa 'alâ rabbînâ tawakkalnâ.",
        translation_fr="Au nom d'Allah nous entrons et au nom d'Allah nous sortons, et sur notre Seigneur nous comptons.",
        source="Sunan Abû Dâwûd 5096",
        order=1,
    ),
    dict(
        category="maison",
        title="Douâa en sortant de chez soi",
        text_ar="بِسْمِ اللَّهِ تَوَكَّلْتُ عَلَى اللَّهِ وَلَا حَوْلَ وَلَا قُوَّةَ إِلَّا بِاللَّهِ",
        transliteration="Bismi llâhi tawakkaltu 'alâ llâhi wa lâ hawla wa lâ quwwata illâ billâh.",
        translation_fr="Au nom d'Allah, je compte sur Allah ; il n'y a de force ni de puissance qu'en Allah.",
        source="Sunan Abû Dâwûd 5095 ; Jâmi' at-Tirmidhî 3426",
        order=2,
    ),
    # ------------------------------------------------------------------
    # Mosquée
    # ------------------------------------------------------------------
    dict(
        category="mosquee",
        title="Douâa en entrant à la mosquée",
        text_ar="اللَّهُمَّ افْتَحْ لِي أَبْوَابَ رَحْمَتِكَ",
        transliteration="Allâhumma ftah lî abwâba rahmatik.",
        translation_fr="Ô Allah, ouvre-moi les portes de Ta miséricorde.",
        source="Sahîh Muslim 713",
        order=1,
    ),
    dict(
        category="mosquee",
        title="Douâa en sortant de la mosquée",
        text_ar="اللَّهُمَّ إِنِّي أَسْأَلُكَ مِنْ فَضْلِكَ وَرَحْمَتِكَ",
        transliteration="Allâhumma innî as'aluka min fadlika wa rahmatik.",
        translation_fr="Ô Allah, je Te demande Ta faveur et Ta miséricorde.",
        source="Sahîh Muslim 713",
        order=2,
    ),
    dict(
        category="mosquee",
        title="Douâa après l'appel à la prière (adhan)",
        text_ar="اللَّهُمَّ رَبَّ هَذِهِ الدَّعْوَةِ التَّامَّةِ وَالصَّلَاةِ الْقَائِمَةِ آتِ مُحَمَّدًا الْوَسِيلَةَ وَالْفَضِيلَةَ وَابْعَثْهُ مَقَامًا مَحْمُودًا الَّذِي وَعَدْتَهُ",
        transliteration="Allâhumma rabba hâdhihi d-da'wati t-tâmmati wa s-salâti l-qâ'imati, âti Muhammadan al-wasîlata wa l-fadîlata wa b'athhu maqâman mahmûdan lladhî wa'adtah.",
        translation_fr="Ô Allah, Seigneur de cet appel parfait et de la prière établie, accorde à Muhammad l'intercession et l'excellence, et élève-le au rang loué que Tu lui as promis.",
        source="Sahîh al-Bukhârî 614",
        order=3,
    ),
    # ------------------------------------------------------------------
    # Protection
    # ------------------------------------------------------------------
    dict(
        category="protection",
        title="Douâa de protection contre le mal",
        text_ar="أَعُوذُ بِعِزَّةِ اللَّهِ وَقُدْرَتِهِ مِنْ شَرِّ مَا أَجِدُ وَأُحَاذِرُ",
        transliteration="A'ûdhu bi 'izzati llâhi wa qudratihi min sharri mâ ajidu wa uhâdhir.",
        translation_fr="Je cherche refuge dans la puissance d'Allah et Sa force contre le mal que je ressens et que je crains.",
        source="Sahîh Muslim 2202",
        order=1,
    ),
    dict(
        category="protection",
        title="Douâa du voyage",
        text_ar="سُبْحَانَ الَّذِي سَخَّرَ لَنَا هَذَا وَمَا كُنَّا لَهُ مُقْرِنِينَ وَإِنَّا إِلَى رَبِّنَا لَمُنْقَلِبُونَ",
        transliteration="Subhâna lladhî sakhkhara lanâ hâdhâ wa mâ kunnâ lahu muqrinîn, wa innâ ilâ rabinâ lamunqalibûn.",
        translation_fr="Gloire à Celui qui a mis ceci à notre service, alors que nous n'aurions pu le dompter ; et c'est vers notre Seigneur que nous retournerons.",
        source="Sunan Abû Dâwûd 2602 ; Jâmi' at-Tirmidhî 3444",
        order=2,
    ),
    # ------------------------------------------------------------------
    # Pardon
    # ------------------------------------------------------------------
    dict(
        category="pardon",
        title="Demander pardon (istighfâr)",
        text_ar="أَسْتَغْفِرُ اللَّهَ الْعَظِيمَ الَّذِي لَا إِلَهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ وَأَتُوبُ إِلَيْهِ",
        transliteration="Astaghfiru llâha l-'azîma lladhî lâ ilâha illâ huwa l-hayyu l-qayyûmu wa atûbu ilayh.",
        translation_fr="Je demande pardon à Allah le Très-Grand, il n'y a de divinité que Lui, le Vivant, l'Éternel, et je me repens vers Lui.",
        source="Sunan Abû Dâwûd 1517",
        order=1,
    ),
    dict(
        category="pardon",
        title="Sayyid al-istighfâr (le maître des demandes de pardon)",
        text_ar="اللَّهُمَّ أَنْتَ رَبِّي لَا إِلَهَ إِلَّا أَنْتَ خَلَقْتَنِي وَأَنَا عَبْدُكَ وَأَنَا عَلَى عَهْدِكَ وَوَعْدِكَ مَا اسْتَطَعْتُ أَعُوذُ بِكَ مِنْ شَرِّ مَا صَنَعْتُ أَبُوءُ لَكَ بِنِعْمَتِكَ عَلَيَّ وَأَبُوءُ بِذَنْبِي فَاغْفِرْ لِي فَإِنَّهُ لَا يَغْفِرُ الذُّنُوبَ إِلَّا أَنْتَ",
        transliteration="Allâhumma anta rabbî lâ ilâha illâ anta, khalaqtanî wa ana 'abduk, wa ana 'alâ 'ahdika wa wa'dika mâ stata't, a'ûdhu bika min sharri mâ sana't, abû'u laka bi ni'matika 'alayya, wa abû'u bi dhanbî, faghfir lî fa innahu lâ yaghfiru d-dhunûba illâ anta.",
        translation_fr="Ô Allah, Tu es mon Seigneur, il n'y a de divinité que Toi. Tu m'as créé et je suis Ton serviteur. Je respecte Ton alliance autant que je peux. Je cherche refuge auprès de Toi contre le mal que j'ai fait. Je reconnais Ta faveur sur moi et je reconnais mon péché. Pardonne-moi, car nul ne pardonne les péchés sauf Toi.",
        source="Sahîh al-Bukhârî 6306",
        order=2,
    ),
    # ------------------------------------------------------------------
    # Vie quotidienne
    # ------------------------------------------------------------------
    dict(
        category="vie",
        title="Douâa pour les parents",
        text_ar="رَبِّ ارْحَمْهُمَا كَمَا رَبَّيَانِي صَغِيرًا",
        transliteration="Rabbi rhamhumâ kamâ rabbayânî saghîrâ.",
        translation_fr="Seigneur, fais-leur miséricorde comme ils m'ont élevé étant petit.",
        source="Coran 17:24 — récitation comme douâa, avec la prière du Prophète ﷺ",
        order=1,
    ),
    dict(
        category="vie",
        title="Douâa de consultation (istikhâra — extrait)",
        text_ar="اللَّهُمَّ إِنِّي أَسْتَخِيرُكَ بِعِلْمِكَ وَأَسْتَقْدِرُكَ بِقُدْرَتِكَ وَأَسْأَلُكَ مِنْ فَضْلِكَ الْعَظِيمِ",
        transliteration="Allâhumma innî astakhîruka bi 'ilmika wa astaqdiruka bi qudratika wa as'aluka min fadlika l-'azîm.",
        translation_fr="Ô Allah, je Te demande de me guider par Ta science, je Te demande de me donner la force par Ta puissance, et je Te demande Ta immense faveur.",
        source="Sahîh al-Bukhârî 1162",
        order=2,
    ),
    dict(
        category="vie",
        title="Réponse à l'éternuement",
        text_ar="يَرْحَمُكَ اللَّهُ",
        transliteration="Yarhamuka llâh.",
        translation_fr="Que Allah te fasse miséricorde. (Le vanter : « Al-hamdu lillâh » — louange à Allah.)",
        source="Sahîh al-Bukhârî 6224",
        order=3,
    ),
]

HADITHS = [
    # ------------------------------------------------------------------
    # Foi & intentions
    # ------------------------------------------------------------------
    dict(
        category="foi",
        title="Les actes valent par les intentions",
        text_ar="إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى",
        translation_fr="Les actes ne valent que par les intentions, et chacun n'aura que ce qu'il a eu l'intention de faire.",
        narrator="'Umar ibn al-Khattâb",
        source="Sahîh al-Bukhârî 1",
        order=1,
    ),
    dict(
        category="foi",
        title="La foi parfaite",
        text_ar="لَا يُؤْمِنُ أَحَدُكُمْ حَتَّى يُحِبَّ لِأَخِيهِ مَا يُحِبُّ لِنَفْسِهِ",
        translation_fr="Nul d'entre vous n'a la foi parfaite tant qu'il n'aime pas pour son frère ce qu'il aime pour lui-même.",
        narrator="Anas ibn Mâlik",
        source="Sahîh al-Bukhârî 13",
        order=2,
    ),
    dict(
        category="foi",
        title="Le bon musulman",
        text_ar="الْمُسْلِمُ مَنْ سَلِمَ الْمُسْلِمُونَ مِنْ لِسَانِهِ وَيَدِهِ",
        translation_fr="Le musulman (parfait) est celui dont les autres musulmans sont à l'abri de sa langue et de sa main.",
        narrator="'Abdullâh ibn 'Amr",
        source="Sahîh al-Bukhârî 10",
        order=3,
    ),
    dict(
        category="foi",
        title="La pudeur est une branche de la foi",
        text_ar="الْحَيَاءُ شُعْبَةٌ مِنَ الْإِيمَانِ",
        translation_fr="La pudeur fait partie de la foi.",
        narrator="Abû Hurayra",
        source="Sahîh al-Bukhârî 9",
        order=4,
    ),
    # ------------------------------------------------------------------
    # Prière & culte
    # ------------------------------------------------------------------
    dict(
        category="priere",
        title="L'acte le plus aimé d'Allah",
        text_ar="أَحَبُّ الْأَعْمَالِ إِلَى اللَّهِ أَدْوَمُهَا وَإِنْ قَلَّ",
        translation_fr="L'acte le plus aimé d'Allah est le plus régulier, même s'il est petit.",
        narrator="'Â'isha",
        source="Sahîh Muslim 783",
        order=1,
    ),
    dict(
        category="priere",
        title="Les cinq prières à leur heure",
        text_ar="أَحَبُّ الْأَعْمَالِ إِلَى اللَّهِ الصَّلَاةُ عَلَى وَقْتِهَا",
        translation_fr="L'acte le plus aimé d'Allah est la prière accomplie à son heure.",
        narrator="'Abdullâh ibn Mas'ûd",
        source="Sahîh al-Bukhârî 527",
        order=2,
    ),
    dict(
        category="priere",
        title="La purification est la moitié de la foi",
        text_ar="الطُّهُورُ شَطْرُ الْإِيمَانِ",
        translation_fr="La purification est la moitié de la foi.",
        narrator="Abû Mâlik al-Ash'arî",
        source="Sahîh Muslim 223",
        order=3,
    ),
    dict(
        category="priere",
        title="Deux mots légères, lourds dans la balance",
        text_ar="كَلِمَتَانِ خَفِيفَتَانِ عَلَى اللِّسَانِ، ثَقِيلَتَانِ فِي الْمِيزَانِ، حَبِيبَتَانِ إِلَى الرَّحْمَنِ: سُبْحَانَ اللَّهِ وَبِحَمْدِهِ، سُبْحَانَ اللَّهِ الْعَظِيمِ",
        translation_fr="Deux paroles légères sur la langue, lourdes dans la balance, aimées du Tout Miséricordieux : « Gloire à Allah et à Lui la louange », « Gloire à Allah le Très-Grand ».",
        narrator="Abû Hurayra",
        source="Sahîh al-Bukhârî 6682",
        order=4,
    ),
    # ------------------------------------------------------------------
    # Morale & comportement
    # ------------------------------------------------------------------
    dict(
        category="morale",
        title="N'est pas de nous celui qui triche",
        text_ar="مَنْ غَشَّ فَلَيْسَ مِنِّي",
        translation_fr="Celui qui triche n'est pas des nôtres.",
        narrator="Abû Hurayra",
        source="Sahîh Muslim 101",
        order=1,
    ),
    dict(
        category="morale",
        title="Ne pas s'occuper de ce qui ne le concerne pas",
        text_ar="مِنْ حُسْنِ إِسْلَامِ الْمَرْءِ تَرْكُهُ مَا لَا يَعْنِيهِ",
        translation_fr="C'est une preuve de la beauté de l'islam d'une personne que de laisser ce qui ne la concerne pas.",
        narrator="Abû Hurayra",
        source="Jâmi' at-Tirmidhî 2317",
        order=2,
    ),
    dict(
        category="morale",
        title="Le meilleur discours",
        text_ar="مَنْ كَانَ يُؤْمِنُ بِاللَّهِ وَالْيَوْمِ الْآخِرِ فَلْيَقُلْ خَيْرًا أَوْ لِيَصْمُتْ",
        translation_fr="Quiconque croit en Allah et au Jour dernier, qu'il dise du bien ou qu'il se taise.",
        narrator="Abû Hurayra",
        source="Sahîh al-Bukhârî 6018",
        order=3,
    ),
    dict(
        category="morale",
        title="La douceur est un don",
        text_ar="إِنَّ اللَّهَ رَفِيقٌ يُحِبُّ الرِّفْقَ فِي الْأَمْرِ كُلِّهِ",
        translation_fr="Allah est Doux, et Il aime la douceur en toute chose.",
        narrator="'Â'isha",
        source="Sahîh Muslim 2165",
        order=4,
    ),
    dict(
        category="morale",
        title="Gratitude envers les gens",
        text_ar="لَا يَشْكُرُ اللَّهَ مَنْ لَا يَشْكُرُ النَّاسَ",
        translation_fr="Celui qui n'est pas reconnaissant envers les gens ne l'est pas envers Allah.",
        narrator="Abû Hurayra",
        source="Sunan Abû Dâwûd 4811 ; Jâmi' at-Tirmidhî 1954",
        order=5,
    ),
    # ------------------------------------------------------------------
    # Bienfaisance
    # ------------------------------------------------------------------
    dict(
        category="bienfaisance",
        title="La bonne parole est une aumône",
        text_ar="وَتَبْسِمُكَ فِي وَجْهِ أَخِيكَ لَكَ صَدَقَةٌ",
        translation_fr="Ton sourire à l'égard de ton frère est une aumône.",
        narrator="Abû Dharr",
        source="Jâmi' at-Tirmidhî 1956",
        order=1,
    ),
    dict(
        category="bienfaisance",
        title="Répandre la salutation",
        text_ar="أَفْشُوا السَّلَامَ بَيْنَكُمْ",
        translation_fr="Répandez la salutation de paix entre vous.",
        narrator="'Abdullâh ibn 'Amr",
        source="Sahîh Muslim 54",
        order=2,
    ),
    dict(
        category="bienfaisance",
        title="La miséricorde envers les créatures",
        text_ar="الرَّاحِمُونَ يَرْحَمُهُمُ الرَّحْمَنُ، ارْحَمُوا مَنْ فِي الْأَرْضِ يَرْحَمْكُمْ مَنْ فِي السَّمَاءِ",
        translation_fr="Les miséricordieux seront traités avec miséricorde par le Tout Miséricordieux. Faites miséricorde à ceux qui sont sur terre, et Celui qui est au ciel vous fera miséricorde.",
        narrator="Abû Hurayra",
        source="Sunan Abû Dâwûd 4942 ; Jâmi' at-Tirmidhî 1924",
        order=3,
    ),
    # ------------------------------------------------------------------
    # Relations & famille
    # ------------------------------------------------------------------
    dict(
        category="relations",
        title="L'ami de chacun",
        text_ar="الْمَرْءُ عَلَى دِينِ خَلِيلِهِ فَلْيَنْظُرْ أَحَدُكُمْ مَنْ يُخَالِلُ",
        translation_fr="Chacun suit la religion de son ami proche ; que chacun d'entre vous regarde avec qui il se lie d'amitié.",
        narrator="Abû Hurayra",
        source="Jâmi' at-Tirmidhî 2378",
        order=1,
    ),
    dict(
        category="relations",
        title="Le meilleur d'entre vous envers sa famille",
        text_ar="خَيْرُكُمْ خَيْرُكُمْ لِأَهْلِهِ وَأَنَا خَيْرُكُمْ لِأَهْلِي",
        translation_fr="Le meilleur d'entre vous est le meilleur envers sa famille, et je suis le meilleur d'entre vous envers ma famille.",
        narrator="Abû Hurayra",
        source="Jâmi' at-Tirmidhî 3895",
        order=2,
    ),
    dict(
        category="relations",
        title="Le conseil est la religion",
        text_ar="الدِّينُ النَّصِيحَةُ",
        translation_fr="La religion est le conseil sincère.",
        narrator="Tamîm ad-Dârî",
        source="Sahîh Muslim 55",
        order=3,
    ),
]
