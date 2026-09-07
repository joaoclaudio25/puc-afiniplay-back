# backend/services/friend_service.py
# Regras de negócio de amigos: cadastro, convite e vínculo automático (nos dois sentidos)
# quando o e-mail de um amigo corresponde a uma conta real no AfiniPlay.

from database import db
from models import Friend, User
from services.email_service import send_email, build_friend_registered_email_html


class FriendService:
    @staticmethod
    def get_all_by_owner(owner_user_id):
        return Friend.query.filter_by(owner_user_id=owner_user_id).order_by(Friend.created_at.desc()).all()

    @staticmethod
    def get_by_id_and_owner(friend_id, owner_user_id):
        return Friend.query.filter_by(id=friend_id, owner_user_id=owner_user_id).first()

    @staticmethod
    def get_registered_by_ids(owner_user_id, friend_ids):
        """Retorna, dentre os ids informados, apenas os amigos do usuário que já
        completaram o cadastro (têm uma conta AfiniPlay vinculada)."""
        return Friend.query.filter(
            Friend.id.in_(friend_ids),
            Friend.owner_user_id == owner_user_id,
            Friend.status == "registered",
        ).all()

    @staticmethod
    def _ensure_registered_link(owner, other_user):
        """Garante que 'owner' tenha 'other_user' como amigo com status 'registered',
        criando o registro se não existir ou atualizando se já existir (ex.: pendente).
        Usado para manter a amizade simétrica: quando duas contas ficam vinculadas por
        e-mail, ambas devem enxergar uma à outra na lista de amigos."""
        entry = Friend.query.filter_by(owner_user_id=owner.id, email=other_user.email).first()
        if entry:
            entry.status = "registered"
            entry.linked_user_id = other_user.id
        else:
            entry = Friend(
                owner_user_id=owner.id,
                name=other_user.full_name or other_user.username,
                email=other_user.email,
                status="registered",
                linked_user_id=other_user.id,
            )
            db.session.add(entry)
        return entry

    @staticmethod
    def create(owner_user_id, name, email, phone):
        """Cria um novo amigo. Evita duplicidade de e-mail para o mesmo dono.
        Se o e-mail já pertencer a uma conta existente no AfiniPlay, o amigo já nasce
        com status 'registered' e a amizade é criada nos dois sentidos."""
        existing = Friend.query.filter_by(owner_user_id=owner_user_id, email=email).first()
        if existing:
            return None, "duplicate"

        existing_user = User.query.filter_by(email=email).first()

        friend = Friend(
            owner_user_id=owner_user_id,
            name=name,
            email=email,
            phone=phone or None,
            status="registered" if existing_user else "pending",
            linked_user_id=existing_user.id if existing_user else None,
        )
        db.session.add(friend)

        if existing_user:
            owner_user = db.session.get(User, owner_user_id)
            if owner_user:
                FriendService._ensure_registered_link(existing_user, owner_user)

        db.session.commit()
        return friend, None

    @staticmethod
    def delete_by_id_and_owner(friend_id, owner_user_id):
        friend = FriendService.get_by_id_and_owner(friend_id, owner_user_id)
        if not friend:
            return False
        db.session.delete(friend)
        db.session.commit()
        return True

    @staticmethod
    def link_registered_friends_to_new_user(new_user):
        """Chamado logo após um novo usuário se cadastrar: procura registros de Friend
        pendentes com o mesmo e-mail (em qualquer conta que o tenha convidado), marca
        como registrado, vincula à nova conta, cria a amizade recíproca (o novo usuário
        também passa a ter quem o convidou como amigo) e avisa por e-mail quem convidou."""
        pending_entries = Friend.query.filter_by(email=new_user.email, status="pending").all()

        for entry in pending_entries:
            entry.status = "registered"
            entry.linked_user_id = new_user.id

            owner = entry.owner
            if owner:
                FriendService._ensure_registered_link(new_user, owner)

            db.session.commit()

            if owner:
                send_email(
                    owner.email,
                    f"{new_user.full_name or new_user.username} aceitou seu convite - AfiniPlay",
                    build_friend_registered_email_html(
                        owner.full_name or owner.username,
                        new_user.full_name or new_user.username,
                    ),
                )

        return pending_entries
