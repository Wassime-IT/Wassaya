from adressBook import AddressBook

book = AddressBook()

while True:
    print("\n===== MENU CARNET D'ADRESSES =====")
    print("1. Ajouter un contact")
    print("2. Supprimer un contact")
    print("3. Afficher les contacts")
    print("4. Quitter")

    choice = input("Votre choix : ")

    if choice == "1":
        nom = input("Nom : ")
        prenom = input("Prénom : ")
        email = input("Email : ")
        phone = input("Téléphone : ")
        book.add_contact(nom, prenom, email, phone)

    elif choice == "2":
        nom = input("Nom du contact à supprimer : ")
        prenom = input("Prénom du contact à supprimer : ")
        book.remove_contact(nom, prenom, email="", phone="")

    elif choice == "3":
        book.display_contacts()

    elif choice == "4":
        print("Au revoir")
        break

    else:
        print("Choix invalide, réessayez")
