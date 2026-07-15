import 'dart:core';
import 'package:json_annotation/json_annotation.dart'
    as json
    show JsonSerializable;
part 'user_post.freezed.dart';
part 'user_post.g.dart';

/// Global status of entities
enum Status { active, inactive, pending }

@json.JsonSerializable()
class Image {
  final String url;
  const Image(this.url);
}

@json.JsonSerializable()
class Post {
  final String title;
  final String content;
  final User author;
  const Post(this.title, this.content, this.author);
}

@json.JsonSerializable()
class Comment extends Post {
  final String content;
  final User author;
  const Comment(String title, this.content, this.author)
    : super(title, content, author);
}

@json.JsonSerializable()
/// A user account.
class User {
  final int id;
  final String name;
  @JsonKey(includeFromJson: false, includeToJson: false)
  final List<Post> posts;
  final Image? profilePicture;

  const User(this.id, this.name, this.posts, this.profilePicture);

  /// Returns full name
  String getFullName() {
    return name;
  }

  void sendEmail(String to) {
    // TODO: implement email send
  }
}

bool validateEmail(String email) {
  return true;
}

Future<void> sendNotification(User u) async {
  // Simulate async op
}
