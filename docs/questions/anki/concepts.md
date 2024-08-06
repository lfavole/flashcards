# Concepts

## Qu'est-ce que la collection Anki ? { id="collection" }

C'est l'ensemble des flashcards que vous devez connaître (Anki se chargera de vous les faire réviser le moment venu).

## Que sont les paquets de cartes ? { id="decks" }

C'est en quelque sorte un dossier qui contient des flashcards qui parlent d'un même sujet (par exemple les capitales des pays ou des questions sur un chapitre de physique).

## Quelle est la différence entre un dossier et un paquet de cartes ? { id="folders" }

Un dossier est en fait un paquet de cartes qui contient des sous-paquets. Ce paquet ne contient en fait rien (et il est préférable de ne rien y mettre) mais, dans le navigateur de cartes, toutes les cartes des sous-paquets y apparaissent.

## Y a-t-il une limite au nombre de niveaux de sous-dossiers ? { id="subfolders-limit" }

Non.

## Que sont les cartes ? { id="cards" }

C'est l'élément que vous révisez, la combinaison d'une question et d'une réponse.

## Quelle est la différence entre une note et une carte ? { id="note-card" }

**Pour les cartes *Basique*, il n'y a pas vraiment de différence entre les cartes et les notes.**

Lorsque vous créez du contenu sur Anki, vous créez en fait des notes. Ce sont en quelque sorte des formulaires remplis avec les informations à savoir.

Mais si vous voulez apprendre des informations qui suivent un même modèle, vous feriez mieux de créer des types de notes avec les champs nécessaires (par exemple *Pays*, *Capitale* et *Continent*). Vous pourrez ensuite créer des modèles de cartes et insérer le contenu des champs aux bons endroits, comme ci-dessous :

<p class="choices">
    <label><input type="radio" name="item" value="0" checked> France</label>
    <label><input type="radio" name="item" value="1"> Italie</label>
    <label><input type="radio" name="item" value="2"> Japon</label>
    <label><input type="radio" name="item" value="3"> Afrique du Sud</label>
    <label><input type="radio" name="item" value="4"> États-Unis</label>
</p>

<script>
document.addEventListener("DOMContentLoaded", function() {
    var fields = document.querySelectorAll(".tabbed-block span:is(.Pays, .Capitale, .Continent)");
    function change() {
        var index = 0;
        for(var item of items) {
            if(item.checked) {
                index = +item.value;
                break;
            }
        }
        var answer = answers[index];
        for(var field of fields) {
            for(var class_ of field.classList) {
                if(class_ in answer) {
                    field.textContent = answers[index][class_];
                    break;
                }
            }
        }
    }

    var answers = [
        {Pays: "France", Capitale: "Paris", Continent: "Europe"},
        {Pays: "Italie", Capitale: "Rome", Continent: "Europe"},
        {Pays: "Japon", Capitale: "Tokyo", Continent: "Asie"},
        {Pays: "Afrique du Sud", Capitale: "Pretoria", Continent: "Afrique"},
        {Pays: "États-Unis", Capitale: "Washington D.C.", Continent: "Amérique"},
    ];
    var items = document.querySelectorAll("input[name=item]");
    for(var item of items) {
        item.addEventListener("change", change);
    }
    change();
});
</script>

<label><input type="radio" class="recto" name="card-side" value="recto" checked> Aperçu du recto</label>
<label><input type="radio" class="verso" name="card-side" value="verso"> Aperçu du verso</label>

=== "Carte 1 : Pays -> capitale"

    Quelle est la capitale du pays **<span class="Pays">{{Pays}}</span>** ?

    ---

    La capitale du pays **<span class="Pays">{{Pays}}</span>** est **<span class="Capitale">{{Capitale}}</span>**.

=== "Carte 2 : Capitale -> pays"

    Quel pays a pour capitale **<span class="Capitale">{{Capitale}}</span>** ?

    ---

    Le pays **<span class="Pays">{{Pays}}</span>** a pour capitale **<span class="Capitale">{{Capitale}}</span>**.

=== "Carte 3 : Pays -> continent"

    Dans quel continent se situe le pays **<span class="Pays">{{Pays}}</span>** ?

    ---

    Le pays **<span class="Pays">{{Pays}}</span>** se situe dans le continent **<span class="Continent">{{Continent}}</span>**.

Cela vous permettra de corriger plus rapidement les fautes d'orthographe dans toutes les cartes et de profiter de certaines fonctionnalités avancées d'Anki.
